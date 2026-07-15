# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
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

### E2E 검증 체크
1. Day7 Pipeline Run에서 `accuracy`와 `roc_auc`를 확인한다.
2. Day8 Model Registry의 Production 버전 URI와 KServe `storageUri`가 일치하는지 확인한다.
3. Day10 `fraud-kfp-route` weight를 `90:10`, `50:50`, `0:100`으로 변경하고 Day7 v1/v2 응답 분포를 확인한다.
4. Day13 Prometheus에서 inference target과 metric을 확인한다.
5. Day13 NeMo Guardrails 정상/민감정보 요청 결과를 비교한다.
6. Day14 OpenShift 토큰으로 MaaS model 목록을 조회하고, 발급된 MaaS API key로 chat completion을 호출한다.

### 공통 추론 요청
```bash
ROUTE=http://$(oc get route fraud-kfp-route -n jukebox -o jsonpath='{.spec.host}')

curl -s -H 'Content-Type: application/json' \
  "$ROUTE/v2/models/fraud/infer" \
  -d @/tmp/python3/fraud-kfp-request.json | jq .
```

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
source /tmp/day8-lineage.env

oc patch isvc day15-broken-model -n jukebox --type=merge \
  -p "{\"spec\":{\"predictor\":{\"model\":{\"storageUri\":\"s3://rhoai-models/${V1_MODEL_PREFIX}\"}}}}"

oc wait --for=condition=Ready isvc/day15-broken-model \
  -n jukebox --timeout=300s
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
