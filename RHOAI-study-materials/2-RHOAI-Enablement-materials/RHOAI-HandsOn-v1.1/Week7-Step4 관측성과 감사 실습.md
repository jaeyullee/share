# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 7 - Step 4 관측성과 감사 로그

> 사전 준비: [Week3 Day13](<Week3-Day13 실습.md>)에서 User Workload Monitoring을 활성화하고 OpenShift Console의 Observe 메뉴에서 PromQL을 실행할 수 있어야 한다.

Kueue와 RHOAI controller 상태를 PrometheusRule로 관측하고, Kubernetes API audit log에서 RHOAI 리소스의 생성·변경·삭제 주체를 추적한다.

### 메트릭 수집 상태 확인

```bash
oc get configmap cluster-monitoring-config \
  -n openshift-monitoring \
  -o jsonpath='{.data.config\.yaml}'
oc get pods -n openshift-user-workload-monitoring
oc get servicemonitor kueue-metrics -n openshift-kueue-operator
```

OpenShift Console에서 **Observe -> Metrics**로 이동해 다음 쿼리를 각각 실행한다.

```promql
max by (cluster_queue, status) (kueue_pending_workloads)
```

```promql
max by (cluster_queue) (kueue_admitted_active_workloads)
```

```promql
max by (deployment) (
  kube_deployment_status_replicas_unavailable{
    namespace="redhat-ods-applications"
  }
)
```

Kueue controller가 HA replica로 실행되므로 `max by`로 중복 series를 합친다. pending 값은 현재 대기 Workload가 없으면 `0`이 정상이다.

### PrometheusRule 생성

Kueue Namespace는 `openshift.io/cluster-monitoring=true`로 cluster monitoring 대상이다. 같은 Namespace에 실습용 rule을 생성한다.

```bash
oc get namespace openshift-kueue-operator --show-labels

oc apply -f - <<'EOF'
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: week7-rhoai-operations
  namespace: openshift-kueue-operator
spec:
  groups:
    - name: week7.rhoai.operations
      rules:
        - record: week7:kueue_pending_workloads:max
          expr: max by (cluster_queue, status) (kueue_pending_workloads)
        - alert: Week7KueuePendingWorkloads
          expr: max by (cluster_queue) (kueue_pending_workloads) > 0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: Kueue ClusterQueue has pending workloads
            description: Check quota, ResourceFlavor and LocalQueue admission.
        - alert: Week7RHOAIComponentUnavailable
          expr: >-
            max by (deployment) (
              kube_deployment_status_replicas_unavailable{
                namespace="redhat-ods-applications"
              }
            ) > 0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: A RHOAI component deployment has unavailable replicas
EOF

oc get prometheusrule week7-rhoai-operations \
  -n openshift-kueue-operator -o yaml
```

Rule을 생성했다고 즉시 Alert가 firing되는 것은 아니다. 조건이 5분간 참일 때만 발생한다. Step 5의 quota 부족 Job을 만든 동안 `Week7KueuePendingWorkloads`를 다시 확인할 수 있다.

### CLI로 Prometheus API 조회

인증서 kubeconfig에는 `oc whoami -t`로 꺼낼 bearer token이 없을 수 있다. 임시 ServiceAccount token을 발급해 Thanos Querier에 전달한다.

```bash
THANOS_HOST="$(oc get route thanos-querier \
  -n openshift-monitoring -o jsonpath='{.spec.host}')"
PROM_TOKEN="$(oc create token prometheus-k8s \
  -n openshift-monitoring --duration=10m)"

curl -sk --oauth2-bearer "$PROM_TOKEN" -G \
  "https://${THANOS_HOST}/api/v1/query" \
  --data-urlencode \
  'query=max by (cluster_queue,status) (kueue_pending_workloads)' | \
  jq '.data.result[] | {metric, value: .value[1]}'

curl -sk --oauth2-bearer "$PROM_TOKEN" -G \
  "https://${THANOS_HOST}/api/v1/query" \
  --data-urlencode \
  'query=week7:kueue_pending_workloads:max' | \
  jq '.data.result[] | {metric, value: .value[1]}'

unset PROM_TOKEN THANOS_HOST
```

PrometheusRule 생성 직후에는 recording rule의 첫 평가가 끝나지 않아 두 번째 쿼리 결과가 비어 있을 수 있다. 약 1분 뒤 다시 조회하고, 계속 비어 있으면 OpenShift Console의 **Observe -> Alerting -> Alerting rules**에서 `week7.rhoai.operations` 그룹의 `health`와 오류를 확인한다.

응답이 HTML이나 `Unauthorized`이면 `jq`가 `Invalid numeric literal`을 출력한다. 이때 query 문제가 아니라 token 또는 URL 문제부터 확인한다. 이 방식은 port-forward를 남기지 않는다.

### 감사 이벤트 생성

```bash
AUDIT_START="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: week7-audit
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: week7-audit-object
  namespace: week7-audit
data:
  stage: created
---
apiVersion: infrastructure.opendatahub.io/v1
kind: HardwareProfile
metadata:
  name: week7-audit-profile
  namespace: week7-audit
  annotations:
    opendatahub.io/display-name: Week7 audit profile
    opendatahub.io/description: Temporary object for audit verification
spec:
  identifiers:
    - identifier: cpu
      displayName: CPU
      resourceType: CPU
      minCount: 1
      maxCount: 2
      defaultCount: 1
    - identifier: memory
      displayName: Memory
      resourceType: Memory
      minCount: 1Gi
      maxCount: 2Gi
      defaultCount: 1Gi
EOF

oc patch configmap week7-audit-object -n week7-audit \
  --type=merge -p '{"data":{"stage":"patched"}}'
oc annotate hardwareprofile week7-audit-profile -n week7-audit \
  week7.example/approved=true
oc delete configmap week7-audit-object -n week7-audit
```

### API audit log 추출

control plane 노드와 audit log 접근 권한을 확인한다.

```bash
CONTROL_PLANE_NODE="$(oc get node \
  -l node-role.kubernetes.io/master \
  -o jsonpath='{.items[0].metadata.name}')"
printf 'CONTROL_PLANE_NODE=%s AUDIT_START=%s\n' \
  "$CONTROL_PLANE_NODE" "$AUDIT_START"
```

Kubernetes API audit log를 JSONL로 필터링한다.

```bash
oc adm node-logs "$CONTROL_PLANE_NODE" \
  --path=kube-apiserver/audit.log | \
  jq -c --arg start "$AUDIT_START" '
    select(.stage == "ResponseComplete")
    | select(.stageTimestamp >= $start)
    | select(
        .objectRef.namespace == "week7-audit"
        or .objectRef.name == "week7-audit"
      )
    | {
        time: .stageTimestamp,
        user: .user.username,
        verb,
        resource: .objectRef.resource,
        namespace: .objectRef.namespace,
        name: .objectRef.name,
        code: .responseStatus.code,
        sourceIPs
      }' > /tmp/week7-audit-events.jsonl

jq . /tmp/week7-audit-events.jsonl
```

출력에서 실행 사용자, `create/patch/delete`, `configmaps`와 `hardwareprofiles`, HTTP 응답 code를 확인한다. 읽기 감사까지 필요하면 audit profile의 level과 저장·보존 정책을 함께 검토해야 한다.

OpenShift API server 자체 리소스의 로그가 필요하면 다음 경로도 같은 방식으로 조회한다.

```bash
oc adm node-logs "$CONTROL_PLANE_NODE" \
  --path=openshift-apiserver/audit.log | tail -n 20
```

### 원복

```bash
oc delete prometheusrule week7-rhoai-operations \
  -n openshift-kueue-operator --ignore-not-found
oc delete namespace week7-audit --wait=true --ignore-not-found
rm -f /tmp/week7-audit-events.jsonl
unset AUDIT_START CONTROL_PLANE_NODE
```

### 공식 문서

- [OpenShift 4.22 - Viewing audit logs](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/security_and_compliance/audit-log-view)
- [OpenShift 4.22 - Monitoring user-defined projects](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/monitoring/configuring-user-workload-monitoring)
- [RHOAI 3.4 - Monitoring your AI systems](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/monitoring_your_ai_systems/index)
