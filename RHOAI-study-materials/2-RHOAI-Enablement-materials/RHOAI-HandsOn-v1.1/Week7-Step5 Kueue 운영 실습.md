# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 7 - Step 5 Kueue 운영과 트러블슈팅

> 사전 준비: [Week3 Day12](<Week3-Day12 실습.md>)의 Kueue 기본 구조와 [Week4 Step3](<Week4-Step3 실습.md>)의 admission·preemption을 이해한 상태에서 진행한다.

DSC가 외부 Kueue를 사용하는 소유권 구조를 확인하고, quota 부족으로 admission이 멈추는 Job을 재현해 Workload condition, event, metric으로 원인을 판정한다.

### 소유권과 Dashboard 설정 확인

```bash
oc get dsc default-dsc \
  -o jsonpath='{.spec.components.kueue.managementState}{"\n"}'
oc get kueues.kueue.openshift.io cluster -o json | jq '{
  managementState: .spec.managementState,
  integrations: .spec.config.integrations.frameworks
}'
oc get deployment kueue-controller-manager \
  -n openshift-kueue-operator
```

정상 구조는 다음과 같다.

- DSC `kueue=Unmanaged`: RHOAI Operator가 Kueue controller를 설치·삭제하지 않음
- Kueue CR `managementState=Managed`: Red Hat build of Kueue Operator가 controller 관리
- integration에 `BatchJob` 포함: Kubernetes Job admission 가능

Dashboard flag의 기존 상태를 저장하고 Kueue UI 연동을 활성화한다.

```bash
oc get odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications -o json | \
  jq -r '
    if .spec.dashboardConfig | has("disableKueue")
    then (.spec.dashboardConfig.disableKueue | tostring)
    else "__ABSENT__"
    end' > /tmp/week7-disable-kueue-before

oc patch odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications --type=merge \
  -p '{"spec":{"dashboardConfig":{"disableKueue":false}}}'
```

`disableKueue=false`는 RHOAI Dashboard의 queue-aware 워크벤치·학습 기능을 켠다. 모든 일반 Kubernetes Job을 RHOAI Dashboard Jobs 목록에 표시한다는 뜻은 아니다.

### 의도적으로 작은 Queue 생성

```bash
oc new-project week7-kueue
oc label namespace week7-kueue kueue.openshift.io/managed=true --overwrite

oc apply -f - <<'EOF'
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata:
  name: week7-cpu
spec:
  nodeLabels:
    lab-role: cpu
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: week7-ops-cq
spec:
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: week7-kueue
  queueingStrategy: BestEffortFIFO
  resourceGroups:
    - coveredResources:
        - cpu
        - memory
      flavors:
        - name: week7-cpu
          resources:
            - name: cpu
              nominalQuota: 500m
            - name: memory
              nominalQuota: 1Gi
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: week7-ops-lq
  namespace: week7-kueue
spec:
  clusterQueue: week7-ops-cq
EOF

oc get clusterqueue week7-ops-cq
oc get localqueue week7-ops-lq -n week7-kueue
```

### admission 실패 재현

Job은 CPU 1개를 요청하지만 Queue quota는 500m뿐이다.

```bash
oc apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: week7-quota-pending
  namespace: week7-kueue
  labels:
    kueue.x-k8s.io/queue-name: week7-ops-lq
spec:
  suspend: true
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: work
          image: registry.redhat.io/ubi9/nginx-126@sha256:10a020f93a6a0c59f0c8d16d3f1cfb7863579dbba847c9ab8bad9fa678a78d1c
          command: [/bin/sh, -c]
          args:
            - echo week7-kueue-admitted; sleep 20
          resources:
            requests:
              cpu: "1"
              memory: 256Mi
            limits:
              cpu: "1"
              memory: 256Mi
EOF

sleep 15
oc get job,workload -n week7-kueue
oc describe workload -n week7-kueue
oc get events -n week7-kueue --sort-by=.lastTimestamp | tail -20
```

정상 실패 상태는 다음과 같다.

- Job: `SUSPENDED=True`
- Workload: `QuotaReserved=False`, `Admitted` condition은 아직 없거나 `False`
- event/message: CPU quota 또는 flavor를 할당할 수 없음
- Pod: 아직 생성되지 않음

Kueue가 Kubernetes Scheduler에 보내기 전에 ResourceFlavor와 quota로 admission을 거부한 상태다. 이 단계에서는 노드에 실제 CPU가 남아 있어도 Job이 실행되지 않는다.

OpenShift Console **Observe -> Metrics**에서 확인한다.

```promql
max by (cluster_queue, status) (
  kueue_pending_workloads{cluster_queue="week7-ops-cq"}
)
```

quota 부족을 판정한 뒤에는 `inadmissible` series가 `1`이다. HA controller의 scrape·상태 전환 시점에 따라 `active=1`이 잠시 함께 보일 수 있으므로 메트릭 하나만으로 판정하지 말고 Workload의 `QuotaReserved=False`와 부족 메시지를 같이 확인한다.

### quota 수정 후 재입장

```bash
oc patch clusterqueue week7-ops-cq --type=json \
  -p '[{
    "op":"replace",
    "path":"/spec/resourceGroups/0/flavors/0/resources/0/nominalQuota",
    "value":"2"
  }]'

oc get job,workload,pod -n week7-kueue
```

Kueue가 quota를 예약하면 Job의 suspend를 해제하고 Pod가 `lab-role=cpu` 노드에 생성된다.

```bash
oc wait job/week7-quota-pending -n week7-kueue \
  --for=condition=Complete --timeout=300s
oc logs job/week7-quota-pending -n week7-kueue
oc get pod -n week7-kueue -o wide
oc describe workload -n week7-kueue | \
  grep -E 'Type:|Status:|Reason:|Message:'
```

예상 로그는 `week7-kueue-admitted`이며 Workload는 `QuotaReserved=True`, `Admitted=True`, `Finished=True`가 된다.

### 운영 판정 순서

Kueue Job이 실행되지 않을 때 다음 순서로 확인한다.

1. Job에 queue label과 `spec.suspend=true`가 있는가.
2. Namespace에 `kueue.openshift.io/managed=true`가 필요한 workload 유형인가.
3. LocalQueue가 존재하고 올바른 ClusterQueue를 참조하는가.
4. ClusterQueue의 `Active=True`와 namespaceSelector가 일치하는가.
5. covered resource, ResourceFlavor, nominal quota가 Pod request를 수용하는가.
6. `Admitted=True` 이후라면 Kubernetes Scheduler의 node selector, taint, allocatable을 확인한다.

`QuotaReserved=False`는 Kueue 단계, `Admitted=True`인데 Pod `Pending`은 Scheduler 단계 문제로 구분한다.

### 원복

```bash
oc delete namespace week7-kueue --wait=true --ignore-not-found
oc delete clusterqueue week7-ops-cq --ignore-not-found
oc delete resourceflavor week7-cpu --ignore-not-found

KUEUE_FLAG="$(cat /tmp/week7-disable-kueue-before)"
case "$KUEUE_FLAG" in
  __ABSENT__)
    oc patch odhdashboardconfig odh-dashboard-config \
      -n redhat-ods-applications --type=json \
      -p '[{"op":"remove","path":"/spec/dashboardConfig/disableKueue"}]' \
      || true
    ;;
  true|false)
    oc patch odhdashboardconfig odh-dashboard-config \
      -n redhat-ods-applications --type=merge \
      -p "{\"spec\":{\"dashboardConfig\":{\"disableKueue\":${KUEUE_FLAG}}}}"
    ;;
esac

rm -f /tmp/week7-disable-kueue-before
unset KUEUE_FLAG
```

DSC `kueue=Unmanaged`와 외부 Kueue Operator는 Week3 Day12 이후의 기본 운영 구성이라 제거하지 않는다.

### 공식 문서

- [RHOAI 3.4 - Managing workloads with Kueue](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/managing_openshift_ai/managing-workloads-with-kueue)
- [Kueue - Troubleshooting](https://kueue.sigs.k8s.io/docs/tasks/troubleshooting/)
