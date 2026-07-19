# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 7 - Step 6 플랫폼과 Dashboard 커스터마이징

> 사전 준비: [Week7 Step0](<Week7-Step0 사전점검 실습.md>)에서 `OdhDashboardConfig`와 `rhods-dashboard` Deployment를 백업한 경로를 현재 셸의 `WEEK7_BACKUP_DIR`에 지정한다.

Dashboard에 사내 도구 타일을 추가하고, 특정 프로젝트에만 보이는 HardwareProfile을 만든 뒤, RHOAI component Deployment resource를 조정하고 원래 값으로 복구한다.

### Dashboard 설정 확인

```bash
test -f "$WEEK7_BACKUP_DIR/odh-dashboard-config.json"
test -f "$WEEK7_BACKUP_DIR/rhods-dashboard.json"

oc get odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications -o json | jq '.spec.dashboardConfig | {
    enablement: (.enablement // true),
    disableProjectScoped: (.disableProjectScoped // false)
  }'
```

`enablement=true`는 사용자가 Applications 타일을 활성화할 수 있게 하고, `disableProjectScoped=false`는 Namespace 범위 Dashboard 리소스를 허용한다.

### 사내 도구 앱 타일 추가

기존 Gitea Route를 사내 도구의 예로 사용한다. OdhApplication은 모델 배포가 아니라 Dashboard launcher metadata다.

```bash
GITEA_HOST="$(oc get route gitea -n gitea -o jsonpath='{.spec.host}')"
test -n "$GITEA_HOST"

# Dashboard creates the success flag after the user clicks Enable.
oc delete configmap week7-gitea-enabled \
  -n redhat-ods-applications --ignore-not-found

oc apply -f - <<EOF
apiVersion: dashboard.opendatahub.io/v1
kind: OdhApplication
metadata:
  name: week7-gitea
  namespace: redhat-ods-applications
  labels:
    app: odh-dashboard
    app.kubernetes.io/part-of: odh-dashboard
spec:
  displayName: Week7 Internal Git
  provider: Platform team
  support: self-managed
  category: Self-managed
  description: Internal Git service used by the RHOAI delivery workflow.
  docsLink: https://docs.gitea.com/
  getStartedLink: https://${GITEA_HOST}/
  getStartedMarkDown: |-
    # Internal Git
    Open the internal Git service used by the RHOAI lab.
  img: >-
    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><rect width="48" height="48" rx="4" fill="#ee0000"/><path d="M12 14h24v5H17v10h14v-4h-7v-5h12v14H12z" fill="white"/></svg>
  route: gitea
  routeNamespace: gitea
  enable:
    validationConfigMap: week7-gitea-enabled
  isEnabled: true
EOF

oc get odhapplication week7-gitea \
  -n redhat-ods-applications -o yaml
```

`validationConfigMap` is the Dashboard activation-result ConfigMap. Do not pre-create it with `enabled: "true"`: Dashboard only recognizes `validation_result: "true"` and will not overwrite an existing ConfigMap. The Enable action creates the correct success flag.

After clicking **Enable**, verify the result directly:

```bash
oc get configmap week7-gitea-enabled \
  -n redhat-ods-applications \
  -o jsonpath='{.data.validation_result}{"\n"}'
```

The expected value is `true`.

RHOAI Dashboard에서 다음을 확인한다.

1. **Applications -> Explore**에서 `Week7 Internal Git` 타일을 찾는다.
2. 타일을 활성화한 뒤 **Applications -> Enabled**에서 확인한다.
3. 타일 링크가 기존 Gitea Route로 열리는지 확인한다.

### 프로젝트 범위 HardwareProfile

```bash
oc get odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications -o json | \
  jq -r '
    if .spec.dashboardConfig | has("disableProjectScoped")
    then (.spec.dashboardConfig.disableProjectScoped | tostring)
    else "__ABSENT__"
    end' > /tmp/week7-disable-project-scoped-before

oc patch odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications --type=merge \
  -p '{"spec":{"dashboardConfig":{"disableProjectScoped":false}}}'

oc new-project week7-custom
oc label namespace week7-custom opendatahub.io/dashboard=true --overwrite

oc apply -f - <<'EOF'
apiVersion: infrastructure.opendatahub.io/v1
kind: HardwareProfile
metadata:
  name: week7-team-small
  namespace: week7-custom
  labels:
    app.kubernetes.io/part-of: hardwareprofile
    app.opendatahub.io/hardwareprofile: "true"
  annotations:
    opendatahub.io/display-name: Week7 team small
    opendatahub.io/description: Project-scoped CPU profile for the Week7 lab.
    opendatahub.io/disabled: "false"
spec:
  identifiers:
    - identifier: cpu
      displayName: CPU
      resourceType: CPU
      minCount: 500m
      maxCount: "2"
      defaultCount: "1"
    - identifier: memory
      displayName: Memory
      resourceType: Memory
      minCount: 1Gi
      maxCount: 4Gi
      defaultCount: 2Gi
EOF

oc get hardwareprofile -n week7-custom
oc get hardwareprofile -n redhat-ods-applications
```

RHOAI Dashboard에서 `week7-custom` 프로젝트를 선택하고 workbench 또는 지원되는 workload 생성 화면에서 `Week7 team small`이 보이는지 확인한다. 다른 프로젝트에서는 이 profile이 보이지 않아야 한다.

### RHOAI component resource 조정

공식 지원 방식은 component Deployment의 container `resources`를 직접 변경하는 것이다. `opendatahub.io/managed: true` annotation이 있으면 Operator가 기본값을 관리하므로 이 실습을 진행하지 않는다.

```bash
oc get deployment rhods-dashboard -n redhat-ods-applications \
  -o json | jq '{
    managed: .metadata.annotations["opendatahub.io/managed"],
    resources: [
      .spec.template.spec.containers[]
      | select(.name == "rhods-dashboard")
      | .resources
    ][0]
  }'

test -z "$(oc get deployment rhods-dashboard \
  -n redhat-ods-applications \
  -o jsonpath='{.metadata.annotations.opendatahub\.io/managed}')"
```

기존 500m CPU request를 550m으로 소폭 변경한다. Dashboard Pod가 재시작되므로 활성 사용자 세션이 없는 시간에 수행한다.

```bash
oc set resources deployment/rhods-dashboard \
  -n redhat-ods-applications \
  --containers=rhods-dashboard \
  --requests=cpu=550m,memory=1Gi \
  --limits=cpu=1,memory=2Gi

oc rollout status deployment/rhods-dashboard \
  -n redhat-ods-applications --timeout=600s

oc get deployment rhods-dashboard -n redhat-ods-applications \
  -o json | jq '
    .spec.template.spec.containers[]
    | select(.name == "rhods-dashboard")
    | .resources'
```

몇 분 뒤 다시 조회해 550m이 유지되면 custom resource가 Operator reconcile에 덮어써지지 않은 것이다. CPU·memory를 무조건 낮추는 것이 목적이 아니라 사용량, restart, latency와 지원 최소값을 근거로 조정하는 것이 목적이다.

### 원복

Dashboard Deployment resource는 Step0의 JSON에서 정확한 원래 값을 읽어 strategic merge patch로 복구한다.

```bash
ORIGINAL_RESOURCES="$(jq -c '
  .spec.template.spec.containers[]
  | select(.name == "rhods-dashboard")
  | .resources' "$WEEK7_BACKUP_DIR/rhods-dashboard.json")"

oc patch deployment rhods-dashboard -n redhat-ods-applications \
  --type=strategic \
  -p "$(jq -n --argjson resources "$ORIGINAL_RESOURCES" '{
    spec: {template: {spec: {containers: [{
      name: "rhods-dashboard",
      resources: $resources
    }]}}}
  }')"

oc rollout status deployment/rhods-dashboard \
  -n redhat-ods-applications --timeout=600s
unset ORIGINAL_RESOURCES
```

프로젝트 범위 flag와 임시 리소스를 복구한다.

```bash
oc delete odhapplication week7-gitea \
  -n redhat-ods-applications --ignore-not-found
oc delete configmap week7-gitea-enabled \
  -n redhat-ods-applications --ignore-not-found
oc delete namespace week7-custom --wait=true --ignore-not-found

PROJECT_FLAG="$(cat /tmp/week7-disable-project-scoped-before)"
case "$PROJECT_FLAG" in
  __ABSENT__)
    oc patch odhdashboardconfig odh-dashboard-config \
      -n redhat-ods-applications --type=json \
      -p '[{"op":"remove","path":"/spec/dashboardConfig/disableProjectScoped"}]' \
      || true
    ;;
  true|false)
    oc patch odhdashboardconfig odh-dashboard-config \
      -n redhat-ods-applications --type=merge \
      -p "{\"spec\":{\"dashboardConfig\":{\"disableProjectScoped\":${PROJECT_FLAG}}}}"
    ;;
esac

rm -f /tmp/week7-disable-project-scoped-before
unset PROJECT_FLAG
```

`opendatahub.io/managed: true`를 실습 중 임의로 추가했다가 `false`로 바꾸거나 annotation만 제거하지 않는다. 공식적인 customization 재활성화 절차는 Deployment 삭제 후 controller의 기본 재생성이다.

### 공식 문서

- [RHOAI 3.4 - Managing applications that show in the dashboard](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/managing_openshift_ai/managing_openshift_ai)
- [RHOAI 3.4 - Customizing the dashboard](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/managing_resources/customizing-the-dashboard)
- [RHOAI 3.4 - Customizing component deployment resources](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/managing_openshift_ai/managing_openshift_ai)
