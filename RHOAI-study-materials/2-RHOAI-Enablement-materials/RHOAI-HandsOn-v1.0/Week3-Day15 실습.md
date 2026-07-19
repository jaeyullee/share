# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 실습
## week 3 - Day15

> 사전 활성화: [Week1 Day1&2 환경 구성](<Week1-Day1&2-환경구성.md#목적별-선택표>)의 목적별 선택표에서 Day6~14에 필요한 Workbench, Pipeline/Registry, KServe, Kueue, Monitoring/Guardrails, MaaS 절을 모두 확인한다.

Day6~14의 훈련, Pipeline, Registry, KServe, RBAC, Kueue, monitoring, Guardrails, MaaS를 연결하고 장애 3종을 주입해서 복구한다.

### 전체 상태 확인
```bash
oc get dsc default-dsc
oc get dspa -n jukebox
oc get modelregistries.modelregistry.opendatahub.io -n rhoai-model-registries
oc get servingruntime,isvc,route -n jukebox
oc get clusterqueue
oc get localqueue,workload -n jukebox
oc get servicemonitor,prometheusrule,nemoguardrails -n jukebox
oc get tenant -n models-as-a-service
oc get maasmodelref -A
oc get maassubscription,maasauthpolicy -n models-as-a-service
```

### 통합 흐름
```text
Workbench/Git
  -> Data Science Pipeline 전처리·훈련·평가
  -> MinIO 모델 파일 저장
  -> Model Registry 버전 등록·Production 승격
  -> KServe RawDeployment
  -> Route weight 무중단 전환
  -> User Workload Monitoring + alert
  -> NeMo Guardrails standalone 검사
  -> GPU LLMInferenceService
  -> Models-as-a-Service subscription/API key/quota
```

### E2E 검증 수행 기준
Day15에서는 Day7~14 리소스를 다시 생성하지 않는다. 각 Day에서 남긴 실행 결과와 현재 운영 리소스를 같은 모델 버전까지 연결해 확인한다. 아래 여섯 절을 순서대로 수행하고, 각 절의 기대 결과를 기록한다.

#### 1. Day7 Pipeline metric과 Run 확인
1. RHOAI 대시보드에서 프로젝트로 `jukebox`를 선택한다.
2. `AI hub` -> `Models` -> `Registry`에서 `fraud-kfp`의 v1/v2를 열고 custom property `kfp_run_name`과 `kfp_run_id`를 기록한다.
3. `Develop & train` -> `Pipelines` -> `Runs`로 이동해 Registry의 `kfp_run_name`과 같은 Run을 찾는다. 기본 실습은 `fraud-n20`과 `fraud-n200`이며, 현재 검증 환경은 `fraud-lineage-v1-n20`과 `fraud-lineage-v2-n200`이다.
4. 각 Run을 열어 상태가 `Succeeded`인지, 입력 parameter의 `n_estimators`가 각각 `20`, `200`인지 확인한다.
5. 두 Run의 체크박스를 선택해 `Compare runs`를 누르고 parameter와 실행 시간을 비교한다.

RHOAI 3.4의 Run 그래프는 ML Metadata DB에 저장된 `system.Metrics`와 `system.Model` custom property를 `Output artifacts`에서 `-`로 표시할 수 있다. 이 표시는 Pipeline version이 오래됐거나 metadata가 저장되지 않았다는 의미가 아니다. Pod를 정리한 뒤에는 단계 로그도 조회되지 않을 수 있으므로, Day15에서는 UI metadata와 로그를 성공 기준으로 사용하지 않는다.

Registry에서 확인한 값을 입력하고 Workflow와 S3 Artifact를 직접 대조한다. `/tmp/day8-lineage.env`는 Bastion 재부팅이나 `/tmp` 정리로 사라질 수 있으므로 Day15의 입력 자료로 사용하지 않는다.

현재 검증 환경의 입력 예시는 다음과 같다. 다른 환경에서는 Registry에 표시된 실제 값을 사용한다.

| 입력 프롬프트 | 현재 검증 환경 값 |
|---|---|
| Registry v1 `kfp_run_name` | `fraud-lineage-v1-n20` |
| Registry v1 `kfp_run_id` | `25ff1b45-9d0d-4285-acfc-fedd88cfda7e` |
| Registry v2 `kfp_run_name` | `fraud-lineage-v2-n200` |
| Registry v2 `kfp_run_id` | `7cfd46e3-af24-4316-b539-3437fbb15a6f` |

명령을 실행하면 네 번 입력을 기다린다. 프롬프트마다 위 표의 값만 입력하고 Enter를 누른다.

```bash
read -rp 'Registry v1 kfp_run_name: ' V1_RUN_NAME
read -rp 'Registry v1 kfp_run_id: ' V1_REGISTRY_RUN_ID
read -rp 'Registry v2 kfp_run_name: ' V2_RUN_NAME
read -rp 'Registry v2 kfp_run_id: ' V2_REGISTRY_RUN_ID

get_latest_workflow() {
  local run_name="$1"
  oc get workflows.argoproj.io -n jukebox -o json | jq -r \
    --arg name "$run_name" '
      [.items[]
       | select(.metadata.annotations["pipelines.kubeflow.org/run_name"] == $name)
       | select(.status.phase == "Succeeded")]
      | sort_by(.metadata.creationTimestamp)
      | last
      | [
          .metadata.name,
          .metadata.labels["pipeline/runid"],
          .status.phase
        ]
      | @tsv'
}

V1_WORKFLOW="$(get_latest_workflow "$V1_RUN_NAME")"
V2_WORKFLOW="$(get_latest_workflow "$V2_RUN_NAME")"
printf 'v1 workflow: %s\nv2 workflow: %s\n' "$V1_WORKFLOW" "$V2_WORKFLOW"

V1_RUN_ID="$(cut -f2 <<<"$V1_WORKFLOW")"
V2_RUN_ID="$(cut -f2 <<<"$V2_WORKFLOW")"
test "$V1_RUN_ID" = "$V1_REGISTRY_RUN_ID"
test "$V2_RUN_ID" = "$V2_REGISTRY_RUN_ID"

V1_KFP_ARTIFACT="$(
  mc find \
    "truenas/rhoai-pipelines/fraud-training-pipeline/${V1_RUN_ID}/train" \
    --name model_out | tail -1
)"
V2_KFP_ARTIFACT="$(
  mc find \
    "truenas/rhoai-pipelines/fraud-training-pipeline/${V2_RUN_ID}/train" \
    --name model_out | tail -1
)"

V1_METRICS_ARTIFACT="$(
  mc find \
    "truenas/rhoai-pipelines/fraud-training-pipeline/${V1_RUN_ID}/evaluate" \
    --name metrics | tail -1
)"
V2_METRICS_ARTIFACT="$(
  mc find \
    "truenas/rhoai-pipelines/fraud-training-pipeline/${V2_RUN_ID}/evaluate" \
    --name metrics | tail -1
)"

test -n "$V1_KFP_ARTIFACT" && test -n "$V2_KFP_ARTIFACT"
test -n "$V1_METRICS_ARTIFACT" && test -n "$V2_METRICS_ARTIFACT"

printf 'v1 metrics: '
mc cat "$V1_METRICS_ARTIFACT" | jq -c .
printf 'v2 metrics: '
mc cat "$V2_METRICS_ARTIFACT" | jq -c .

V1_MODEL_SHA256="$(mc cat "$V1_KFP_ARTIFACT" | sha256sum | awk '{print $1}')"
V2_MODEL_SHA256="$(mc cat "$V2_KFP_ARTIFACT" | sha256sum | awk '{print $1}')"
printf 'v1 model sha256=%s\nv2 model sha256=%s\n' \
  "$V1_MODEL_SHA256" "$V2_MODEL_SHA256"
```

두 Workflow의 `PHASE`가 `Succeeded`여야 하고 두 metrics Artifact에서 `accuracy`, `roc_auc`가 출력돼야 한다. 현재 검증 환경에서는 v1이 `accuracy=0.971`, `roc_auc=0.660915`, v2가 `accuracy=0.973`, `roc_auc=0.745676`이다. 데이터와 package가 달라지면 값도 달라질 수 있으므로 절댓값보다 `V1_RUN_ID`/`V2_RUN_ID`, S3 Artifact, Registry version이 같은 lineage를 가리키는지가 우선이다.

`n_estimators`, `random_state`, `sha256`은 다음 절에서 Registry v1/v2 custom property로 확인한다. Registry의 `sha256`은 위에서 S3 `model_out`을 직접 계산한 값과 같아야 한다.

#### 2. Day8 Registry version과 KServe storageUri 비교
1. RHOAI 대시보드에서 `AI hub` -> `Models` -> `Registry`로 이동한다.
2. `jukebox-registry`의 Registered Model `fraud-kfp`를 연다.
3. v1과 v2에서 Version ID, `kfp_run_name`, `kfp_run_id`, `n_estimators`, `random_state`, `sha256`, `stage`, 모델 위치를 확인한다.
4. Day10 전환 완료 상태라면 v1의 `stage=Archived`, v2의 `stage=Production`이어야 한다. 기본 필드 `state`는 두 버전 모두 롤백 가능한 `LIVE` 상태로 남아 있을 수 있다.

KServe가 참조하는 Registry ID와 S3 경로를 출력한다.

```bash
oc get isvc fraud-kfp-v1 fraud-kfp-v2 -n jukebox -o json | jq -r '
  .items[] |
  [
    .metadata.name,
    .metadata.annotations["modelregistry.opendatahub.io/registered-model-id"],
    .metadata.annotations["modelregistry.opendatahub.io/model-version-id"],
    .spec.predictor.model.storageUri,
    (.status.conditions[] | select(.type == "Ready") | .status)
  ] | @tsv'
```

각 행은 `InferenceService`, Registered Model ID, Model Version ID, `storageUri`, Ready 상태 순서다. 다음 항목을 대조한다.

| Registry 화면 | InferenceService |
|---|---|
| `fraud-kfp` ID | `registered-model-id` annotation |
| v1/v2 Version ID | `model-version-id` annotation |
| Bucket `rhoai-models` + Path `<prefix>/model.joblib` | `storageUri=s3://rhoai-models/<prefix>` |

Registry는 파일까지 가리키고 KServe는 모델 디렉터리를 가리키므로 문자열이 완전히 같지는 않다. Registry 위치가 `KServe storageUri + /model.joblib`이면 같은 artifact다. 실제 S3 객체도 확인한다.

```bash
for name in fraud-kfp-v1 fraud-kfp-v2; do
  uri=$(oc get isvc "$name" -n jukebox \
    -o jsonpath='{.spec.predictor.model.storageUri}')
  echo "$name -> $uri/model.joblib"
  mc stat "truenas/${uri#s3://}/model.joblib"
done
unset uri name
```

두 InferenceService가 `Ready=True`이고 Registry ID, S3 prefix, SHA-256이 Day7에서 선택한 v1/v2 Run과 각각 연결되면 통과다.

#### 3. Day10 Route weight와 응답 분포 확인
먼저 직접 backend 응답을 구분할 입력 파일을 다시 만든다. 이 데이터는 검증 환경에서 v1이 `1`, v2가 `0`을 반환한다.

```bash
mkdir -p /tmp/python3
cat > /tmp/python3/fraud-kfp-request.json <<'EOF'
{
  "inputs": [
    {
      "name": "input-0",
      "shape": [1, 7],
      "datatype": "FP32",
      "data": [3672.37, 22.0, 1.0, 3.0, 440.0, 53.2, 0.0]
    }
  ]
}
EOF
```

Route 분포를 해석하기 전에 각 backend의 현재 prediction을 직접 확인한다. 임시 port-forward는 검증 직후 종료한다.

```bash
cleanup_day15_backend_pf() {
  for pid in "${V1_PF_PID:-}" "${V2_PF_PID:-}"; do
    if test -n "$pid"; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup_day15_backend_pf EXIT INT TERM

oc port-forward -n jukebox deploy/fraud-kfp-v1-predictor \
  18181:8080 >/tmp/day15-v1-port-forward.log 2>&1 &
V1_PF_PID=$!
oc port-forward -n jukebox deploy/fraud-kfp-v2-predictor \
  18182:8080 >/tmp/day15-v2-port-forward.log 2>&1 &
V2_PF_PID=$!
sleep 3

V1_PREDICTION=$(curl -fsS -H 'Content-Type: application/json' \
  http://127.0.0.1:18181/v2/models/fraud/infer \
  -d @/tmp/python3/fraud-kfp-request.json | jq -r '.outputs[0].data[0]')
V2_PREDICTION=$(curl -fsS -H 'Content-Type: application/json' \
  http://127.0.0.1:18182/v2/models/fraud/infer \
  -d @/tmp/python3/fraud-kfp-request.json | jq -r '.outputs[0].data[0]')

printf 'v1 prediction=%s\nv2 prediction=%s\n' \
  "$V1_PREDICTION" "$V2_PREDICTION"

cleanup_day15_backend_pf
trap - EXIT INT TERM
unset V1_PF_PID V2_PF_PID
unset -f cleanup_day15_backend_pf
```

`fraud-kfp-route`는 Day10의 `jukebox-serving` Application이 self-heal한다. 직접 Route를 변경하면 Git의 `0:100`으로 복구되므로, 분포 검증 동안만 self-heal을 끄고 종료 시 반드시 `0:100`과 self-heal을 복구한다.

```bash
(
set -euo pipefail

APP=jukebox-serving
ROUTE_NAME=fraud-kfp-route
ROUTE_URL="http://$(oc get route "$ROUTE_NAME" -n jukebox \
  -o jsonpath='{.spec.host}')"

# 시작 상태가 Day10 Git 선언과 일치하는지 확인한다.
oc get applications.argoproj.io "$APP" -n openshift-gitops \
  -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status
oc get route "$ROUTE_NAME" -n jukebox \
  -o jsonpath='{.spec.to.name}={.spec.to.weight}{" "}{range .spec.alternateBackends[*]}{.name}={.weight}{" "}{end}{"\n"}'

restore_day15_route() {
  oc patch route "$ROUTE_NAME" -n jukebox --type=merge \
    -p '{"spec":{"to":{"weight":0},"alternateBackends":[{"kind":"Service","name":"fraud-kfp-v2-predictor","weight":100}]}}' \
    >/dev/null
  oc patch applications.argoproj.io "$APP" -n openshift-gitops \
    --type=merge \
    -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":true}}}}' \
    >/dev/null
  oc annotate applications.argoproj.io "$APP" -n openshift-gitops \
    argocd.argoproj.io/refresh=hard --overwrite >/dev/null
}
trap restore_day15_route EXIT INT TERM

oc patch applications.argoproj.io "$APP" -n openshift-gitops \
  --type=merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":false,"selfHeal":false}}}}'

sample_route() {
  v1_weight=$1
  v2_weight=$2
  requests=$3
  patch=$(jq -n \
    --argjson v1 "$v1_weight" \
    --argjson v2 "$v2_weight" \
    '{spec:{to:{weight:$v1},alternateBackends:[{
      kind:"Service",name:"fraud-kfp-v2-predictor",weight:$v2
    }]}}')

  oc patch route "$ROUTE_NAME" -n jukebox --type=merge -p "$patch"
  sleep 10
  printf '\nweight v1:v2=%s:%s\n' "$v1_weight" "$v2_weight"
  oc get route "$ROUTE_NAME" -n jukebox \
    -o jsonpath='{.spec.to.name}={.spec.to.weight}{" "}{range .spec.alternateBackends[*]}{.name}={.weight}{" "}{end}{"\n"}'

  for i in $(seq 1 "$requests"); do
    curl -fsS -H 'Content-Type: application/json' \
      "$ROUTE_URL/v2/models/fraud/infer" \
      -d @/tmp/python3/fraud-kfp-request.json |
      jq -r '.outputs[0].data[0]'
  done | sort | uniq -c
}

sample_route 90 10 40
sample_route 50 50 40
sample_route 0 100 10

# Git 선언 상태와 self-heal을 명시적으로 복구한다.
restore_day15_route
trap - EXIT INT TERM
sleep 10

oc get applications.argoproj.io "$APP" -n openshift-gitops \
  -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status
oc get route "$ROUTE_NAME" -n jukebox \
  -o jsonpath='{.spec.to.name}={.spec.to.weight}{" "}{range .spec.alternateBackends[*]}{.name}={.weight}{" "}{end}{"\n"}'
)
```

예상 해석은 다음과 같다.

- `90:10`: v1 prediction이 약 36회, v2 prediction이 약 4회에 가깝다.
- `50:50`: 두 prediction 수가 비슷하다.
- `0:100`: 10회 모두 v2 prediction이다.
- 표본 수가 적으므로 90:10과 50:50이 정확히 일치할 필요는 없다.
- 마지막 출력은 Application `Synced/Healthy`, Route `v1=0`, `v2=100`이어야 한다.

#### 4. Day13 Prometheus target과 inference metric 확인
먼저 현재 v2 Route로 추론 traffic을 추가 생성한다.

```bash
ROUTE_URL="http://$(oc get route fraud-kfp-route -n jukebox \
  -o jsonpath='{.spec.host}')"

for i in $(seq 1 30); do
  curl -fsS -o /dev/null -H 'Content-Type: application/json' \
    "$ROUTE_URL/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-kfp-request.json
done
```

OpenShift Console에서 다음 순서로 확인한다.

1. `Observe` -> `Targets`로 이동한다.
2. 검색창에 `fraud-kfp`를 입력한다.
3. `jukebox/fraud-kfp-v1-metrics`와 `jukebox/fraud-kfp-v2-metrics` target이 `Up`인지 확인한다.
4. `Observe` -> `Metrics`로 이동한다.
5. 다음 PromQL을 차례로 실행한다.

두 inference target의 scrape 상태를 확인한다.

```promql
up{namespace="jukebox", service=~"fraud-kfp-v[12]-metrics"}
```

각 시계열 값이 `1`이어야 한다. 누적 추론 요청 수와 성공 요청 수를 확인한다.

```promql
sum by (service) (
  model_infer_request_duration_count{
    namespace="jukebox",
    service=~"fraud-kfp-v[12]-metrics"
  }
)
```

```promql
sum by (service) (
  model_infer_request_success_total{
    namespace="jukebox",
    service=~"fraud-kfp-v[12]-metrics"
  }
)
```

Route 분포 검증을 수행했다면 두 Service의 count가 모두 존재해야 하고, 마지막 30회 요청 때문에 v2 count가 추가 증가해야 한다. target이 없으면 ServiceMonitor selector와 metric Service를 확인하고, target은 `Up`인데 count가 없으면 추론 요청 URL과 응답 상태를 확인한다.

```bash
oc get servicemonitor fraud-kfp-v1-metrics fraud-kfp-v2-metrics \
  -n jukebox
oc get svc fraud-kfp-v1-metrics fraud-kfp-v2-metrics -n jukebox
```

#### 5. Day13 NeMo Guardrails 정상/민감정보 요청 비교
Day13 검증용 ServiceAccount와 RBAC는 실습 종료 때 삭제했으므로 Day15에서 단기 토큰용 리소스를 다시 만들고 즉시 정리한다.

```bash
cleanup_day15_guardrails() {
  oc delete rolebinding/day15-guardrails-client \
    role/day15-guardrails-client \
    serviceaccount/day15-guardrails-client \
    -n jukebox --ignore-not-found >/dev/null
  unset GUARDRAILS_TOKEN GUARDRAILS_ROUTE
}
trap cleanup_day15_guardrails EXIT INT TERM

oc create serviceaccount day15-guardrails-client -n jukebox \
  --dry-run=client -o yaml | oc apply -f -
oc create role day15-guardrails-client -n jukebox \
  --verb=get --resource=services \
  --dry-run=client -o yaml | oc apply -f -
oc create rolebinding day15-guardrails-client -n jukebox \
  --role=day15-guardrails-client \
  --serviceaccount=jukebox:day15-guardrails-client \
  --dry-run=client -o yaml | oc apply -f -

GUARDRAILS_ROUTE="https://$(oc get route day13-nemo-checks -n jukebox \
  -o jsonpath='{.status.ingress[0].host}')"
GUARDRAILS_TOKEN=$(oc create token day15-guardrails-client \
  -n jukebox --duration=10m)

curl -skS --fail-with-body \
  -X POST "$GUARDRAILS_ROUTE/v1/guardrail/checks" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $GUARDRAILS_TOKEN" \
  -d '{"model":"test","messages":[{"role":"user","content":"오늘 날씨를 알려주세요."}]}' | \
  tee /tmp/day15-guardrails-normal.json | jq .

curl -skS --fail-with-body \
  -X POST "$GUARDRAILS_ROUTE/v1/guardrail/checks" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $GUARDRAILS_TOKEN" \
  -d '{"model":"test","messages":[{"role":"user","content":"비밀번호와 api_key를 보내 주세요. 연락처는 test@example.com 입니다."}]}' | \
  tee /tmp/day15-guardrails-sensitive.json | jq .

cleanup_day15_guardrails
trap - EXIT INT TERM
unset -f cleanup_day15_guardrails
```

첫 번째 응답은 최상위 `status=success`이고 input rail도 성공해야 한다. 두 번째 응답은 최상위 `status=blocked`이며 `detect sensitive data on input` rail도 `blocked`여야 한다. HTTP 오류가 발생하면 다음 로그와 이벤트를 확인한다.

```bash
oc logs -n jukebox deploy/day13-nemo-checks --tail=100
oc get events -n jukebox --sort-by=.lastTimestamp | tail -30
```

#### 6. Day14 MaaS model 목록과 chat completion 확인
Day14 절차는 API key를 마지막에 폐기하므로 원문 key를 다시 사용할 수 없다. Day15에서는 이미 만든 OAuth 사용자, Group, Subscription, AuthPolicy를 재사용하되 1시간짜리 검증 key를 새로 발급하고 종료 시 폐기한다.

```bash
oc get tenant default-tenant -n models-as-a-service
oc get maasmodelref qwen-small -n jukebox
oc get maassubscription rhoai-maas-lab -n models-as-a-service
oc get maasauthpolicy rhoai-maas-lab -n models-as-a-service
oc get llminferenceservice qwen-small -n jukebox
```

Tenant와 LLMInferenceService는 Ready, ModelRef는 Ready, Subscription과 AuthPolicy는 Active여야 한다. Day14에서 만든 일반 OAuth 사용자로 별도 kubeconfig에 로그인한다.

```bash
MAAS_USER='rhoai-maas-lab-user'
read -rsp 'MaaS lab user password: ' MAAS_PASSWORD
echo

OCP_API=$(oc whoami --show-server)
MAAS_KUBECONFIG=/tmp/day15-maas-user.kubeconfig
rm -f "$MAAS_KUBECONFIG"

KUBECONFIG="$MAAS_KUBECONFIG" oc login "$OCP_API" \
  -u "$MAAS_USER" -p "$MAAS_PASSWORD"
OPENSHIFT_TOKEN=$(KUBECONFIG="$MAAS_KUBECONFIG" oc whoami -t)

cleanup_day15_maas() {
  if test -n "${MAAS_API_KEY_ID:-}" && \
     test -n "${OPENSHIFT_TOKEN:-}"; then
    curl -sk -X DELETE \
      -H "Authorization: Bearer $OPENSHIFT_TOKEN" \
      "https://maas.apps.sno.ocp422.com/maas-api/v1/api-keys/$MAAS_API_KEY_ID" \
      >/dev/null || true
  fi
  rm -f "${MAAS_KUBECONFIG:-/tmp/day15-maas-user.kubeconfig}"
  unset API_KEY_RESPONSE MAAS_API_KEY MAAS_API_KEY_ID OPENSHIFT_TOKEN
  unset DAY15_KEY_NAME DAY15_KEY_PAYLOAD
  unset MAAS_PASSWORD MAAS_KUBECONFIG MAAS_USER OCP_API
}
trap cleanup_day15_maas EXIT INT TERM
```

OpenShift token으로 현재 사용자가 접근 가능한 MaaS model 목록을 확인한다.

```bash
curl -skS --fail-with-body \
  -H "Authorization: Bearer $OPENSHIFT_TOKEN" \
  https://maas.apps.sno.ocp422.com/maas-api/v1/models | \
  tee /tmp/day15-maas-models.json | jq .
```

목록에 `jukebox/qwen-small`이 있어야 한다. Day15용 API key를 발급한다.

```bash
DAY15_KEY_NAME="day15-e2e-$(date +%Y%m%d-%H%M%S)"
DAY15_KEY_PAYLOAD=$(jq -n --arg name "$DAY15_KEY_NAME" '{
  name:$name,
  description:"Day15 E2E validation",
  subscription:"rhoai-maas-lab",
  expiresIn:"1h"
}')

API_KEY_RESPONSE=$(curl -skS --fail-with-body -X POST \
  https://maas.apps.sno.ocp422.com/maas-api/v1/api-keys \
  -H "Authorization: Bearer $OPENSHIFT_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "$DAY15_KEY_PAYLOAD")

MAAS_API_KEY=$(jq -r '.key' <<<"$API_KEY_RESPONSE")
MAAS_API_KEY_ID=$(jq -r '.id' <<<"$API_KEY_RESPONSE")
test "${MAAS_API_KEY#sk-oai-}" != "$MAAS_API_KEY"
test -n "$MAAS_API_KEY_ID"
```

발급된 key로 OpenAI 호환 chat completion을 호출한다.

```bash
curl -skS --fail-with-body \
  https://maas.apps.sno.ocp422.com/jukebox/qwen-small/v1/chat/completions \
  -H "Authorization: Bearer $MAAS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5-0.5b-instruct","messages":[{"role":"user","content":"한 문장으로 자기소개해 주세요."}],"max_tokens":64}' | \
  tee /tmp/day15-maas-chat.json | jq .
```

HTTP 200 응답과 `.choices[0].message.content`의 생성 문장을 확인하면 통과다. 검증 key를 폐기하고 폐기 후 403도 확인한다.

```bash
curl -skS --fail-with-body -X DELETE \
  -H "Authorization: Bearer $OPENSHIFT_TOKEN" \
  "https://maas.apps.sno.ocp422.com/maas-api/v1/api-keys/$MAAS_API_KEY_ID" | jq .
MAAS_API_KEY_ID=

curl -sk -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer $MAAS_API_KEY" \
  https://maas.apps.sno.ocp422.com/maas-api/v1/models

cleanup_day15_maas
trap - EXIT INT TERM
unset -f cleanup_day15_maas
unset ROUTE_URL
```

마지막 HTTP 상태가 `403`이어야 폐기가 완료된 것이다. API key 원문과 OAuth 비밀번호는 문서, 파일, shell history에 기록하지 않는다.

## 장애 1 - Pipeline 입력 경로 오류

### 장애 주입
Day7 Pipeline Run의 `dataset_uri`를 다음처럼 존재하지 않는 경로로 변경한다.

```text
s3://rhoai-pipelines/input/not-found.csv
```

### 진단
```bash
oc get workflows.argoproj.io -n jukebox
oc get pods -n jukebox | grep fraud-training
oc logs -n jukebox <FAILED_PIPELINE_POD> --all-containers
mc stat truenas/rhoai-pipelines/input/not-found.csv
```

### 복구
`dataset_uri`를 정상 경로로 되돌리고 새 Run을 생성한다.

```text
s3://rhoai-pipelines/input/fraud_sample.csv
```

이전 실패 Run을 수정하는 것이 아니라 같은 Pipeline version과 정상 parameter로 새 Run을 실행한다.

## 장애 2 - InferenceService Not Ready

### 장애 주입
운영 중인 기존 모델을 건드리지 않고 장애 재현용 InferenceService를 만든다.

```bash
oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: day15-broken-model
  namespace: jukebox
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    serviceAccountName: kserve-sa
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
        version: "1"
      runtime: mlserver-sklearn
      storageUri: s3://rhoai-models/not-found
EOF
```

### 진단
```bash
oc get isvc day15-broken-model -n jukebox
oc describe isvc day15-broken-model -n jukebox
oc get pods -n jukebox -l serving.kserve.io/inferenceservice=day15-broken-model
oc logs deploy/day15-broken-model-predictor \
  -n jukebox -c storage-initializer
oc get events -n jukebox --sort-by=.lastTimestamp | tail -30
```

### 복구
```bash
V1_STORAGE_URI="$(oc get isvc fraud-kfp-v1 -n jukebox \
  -o jsonpath='{.spec.predictor.model.storageUri}')"
test -n "$V1_STORAGE_URI"

oc patch isvc day15-broken-model -n jukebox --type=merge \
  -p "{\"spec\":{\"predictor\":{\"model\":{\"storageUri\":\"${V1_STORAGE_URI}\"}}}}"

oc wait --for=condition=Ready isvc/day15-broken-model \
  -n jukebox --timeout=300s

unset V1_STORAGE_URI
```

복구 후 `storage-initializer`와 model server 로그가 정상인지 확인한다.

## 장애 3 - ResourceQuota 부족과 Kueue 대기

### ResourceQuota 거부 재현
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: day15-quota-fail
  namespace: jukebox-team-a
spec:
  restartPolicy: Never
  containers:
    - name: check
      image: registry.redhat.io/rhoai/odh-pipeline-runtime-datascience-cpu-py312-rhel9@sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661
      command: ["sleep", "300"]
      resources:
        requests: {cpu: "5", memory: 1Gi}
        limits: {cpu: "5", memory: 1Gi}
EOF

oc describe resourcequota team-a-quota -n jukebox-team-a
oc get events -n jukebox-team-a --sort-by=.lastTimestamp | tail -20
```

### 복구
요청을 quota 이내로 줄여 다시 생성한다.

```bash
oc delete pod day15-quota-fail -n jukebox-team-a --ignore-not-found
oc apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: day15-quota-ok
  namespace: jukebox-team-a
spec:
  restartPolicy: Never
  containers:
    - name: check
      image: registry.redhat.io/rhoai/odh-pipeline-runtime-datascience-cpu-py312-rhel9@sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661
      command: ["sleep", "60"]
      resources:
        requests: {cpu: 500m, memory: 512Mi}
        limits: {cpu: 500m, memory: 512Mi}
EOF

oc wait --for=condition=Ready pod/day15-quota-ok \
  -n jukebox-team-a --timeout=180s
```

### Kueue와 차이 확인
ResourceQuota 초과는 API admission에서 즉시 거부된다. Kueue quota 부족은 workload가 생성된 뒤 queue에서 대기한다.

```bash
oc get workload -n jukebox
oc describe clusterqueue team-cq
oc describe localqueue team-lq -n jukebox
```

## 고객 시나리오 정리

### 금융 사기탐지
| 요구사항 | 적용 기능 |
|---|---|
| 모델 재현 | Workbench + Pipeline |
| 버전 승인 | Model Registry custom property |
| 무중단 교체 | RawDeployment 2개 + Route weight |
| 팀 격리 | RBAC + Secret + ResourceQuota |
| 운영 감시 | UWM + ServiceMonitor + PrometheusRule |

### 제조 품질검사
표형 데이터는 fraud pipeline의 feature schema를 품질 측정값으로 교체한다. 이미지 모델은 GPU HardwareProfile과 GPU queue를 사용하고 ServingRuntime 지원 형식을 확인한다.

### 사내 LLM 서비스
| 요구사항 | 적용 기능 |
|---|---|
| GPU LLM 실행 | LLMInferenceService |
| 공통 endpoint | MaaS gateway |
| 사용자 접근 | MaaS API key + MaaSAuthPolicy |
| 사용 한도 | MaaSSubscription tokenRateLimits |
| 입력 안전 | NeMo Guardrails |
| 사용량 | MaaS/Prometheus metric |

## 최종 산출물
1. Day7 Pipeline Run 비교 화면과 평가 metric
2. Day8 Registry v1/v2와 Production 승격 기록
3. Day10 GitOps sync/self-heal 결과
4. Day12 Kueue admission/priority 이벤트
5. Day13 PromQL과 Guardrails 정상/차단 응답
6. Day14 MaaS model/subscription/policy/API key 호출 결과
7. 장애 3종의 증상, 진단 명령, 원인, 복구 결과

### 실습용 장애 리소스 정리
```bash
oc delete isvc day15-broken-model -n jukebox --ignore-not-found
oc delete pod day15-quota-ok day15-quota-fail \
  -n jukebox-team-a --ignore-not-found
```

Day1~14에서 생성한 학습 리소스는 복습에 사용하므로 Day15에서 일괄 삭제하지 않는다. 전체 초기화가 필요하면 Namespace, cluster-scoped queue, DSC 설정, Operator를 구분해서 별도 정리한다.
