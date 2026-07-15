# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day8

> 사전 활성화: [Week1 Day1&2 - AI Pipelines와 Model Registry 구성](<Week1-Day1&2-환경구성.md#ai-pipelines와-model-registry-구성>), [KServe RawDeployment 구성](<Week1-Day1&2-환경구성.md#kserve-rawdeployment-구성>), [Week2 Day7](<Week2-Day7 실습.md>)의 성공한 `fraud-n20`·`fraud-n200` KFP Run을 먼저 확인한다.

Day7 KFP가 생성한 Model artifact를 서빙용 S3 경로로 승격하고, 동일 artifact를 Model Registry v1/v2와 KServe InferenceService에 연결한다.

> Model Registry는 모델 파일 자체를 보관하지 않는다. 실제 `joblib` 파일은 MinIO S3에 있고 Registry에는 모델 이름, 버전, 성능, KFP Run ID, 해시와 S3 위치를 기록한다.

### Day7 lineage 불러오기
Day7에서 만든 `/tmp/day7-lineage.env`가 있으면 불러온다.

```bash
test -s /tmp/day7-lineage.env
source /tmp/day7-lineage.env

printf 'v1 run=%s id=%s artifact=%s\n' \
  "$V1_RUN_NAME" "$V1_RUN_ID" "$V1_KFP_ARTIFACT"
printf 'v2 run=%s id=%s artifact=%s\n' \
  "$V2_RUN_NAME" "$V2_RUN_ID" "$V2_KFP_ARTIFACT"
```

파일이 없으면 Day7의 **Day8에서 사용할 baseline과 candidate 확정** 절을 다시 실행한다. 이 실습의 버전 매핑은 다음과 같다.

| Registry 버전 | Day7 KFP Run | 역할 |
|---|---|---|
| v1 | `fraud-n20` | 현재 운영 중인 baseline |
| v2 | `fraud-n200` | 새로 검증할 candidate |

`n_estimators=200`이 항상 더 우수하다는 의미는 아니다. v1/v2는 동일 훈련 파이프라인에서 생성된 서로 다른 artifact의 lifecycle과 트래픽 전환을 보기 위한 버전 구분이다.

### KFP metric artifact 확인
각 Run의 평가 결과를 MinIO에서 읽는다.

```bash
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

test -n "$V1_METRICS_ARTIFACT"
test -n "$V2_METRICS_ARTIFACT"

V1_METRICS="$(mc cat "$V1_METRICS_ARTIFACT")"
V2_METRICS="$(mc cat "$V2_METRICS_ARTIFACT")"

V1_ACCURACY="$(jq -r '.accuracy' <<<"$V1_METRICS")"
V1_ROC_AUC="$(jq -r '.roc_auc' <<<"$V1_METRICS")"
V2_ACCURACY="$(jq -r '.accuracy' <<<"$V2_METRICS")"
V2_ROC_AUC="$(jq -r '.roc_auc' <<<"$V2_METRICS")"

printf 'v1 accuracy=%s roc_auc=%s\n' "$V1_ACCURACY" "$V1_ROC_AUC"
printf 'v2 accuracy=%s roc_auc=%s\n' "$V2_ACCURACY" "$V2_ROC_AUC"
```

값은 Day7 Run 비교 화면의 `accuracy`, `roc_auc`와 같아야 한다.

### KFP artifact를 서빙용 S3 경로로 승격
KFP Artifact Store의 `model_out`은 Run UUID가 포함된 내부 경로에 있다. Registry와 KServe가 장기간 참조할 수 있도록 `rhoai-models` 버킷의 버전별 경로로 복사한다. Run ID를 경로에 포함해 이미 등록된 모델 파일을 덮어쓰지 않는다.

```bash
mc mb --ignore-existing truenas/rhoai-models

V1_MODEL_PREFIX="fraud-kfp/v1-${V1_RUN_ID}"
V2_MODEL_PREFIX="fraud-kfp/v2-${V2_RUN_ID}"

mc cp "$V1_KFP_ARTIFACT" \
  "truenas/rhoai-models/${V1_MODEL_PREFIX}/model.joblib"
mc cp "$V2_KFP_ARTIFACT" \
  "truenas/rhoai-models/${V2_MODEL_PREFIX}/model.joblib"

mc stat "truenas/rhoai-models/${V1_MODEL_PREFIX}/model.joblib"
mc stat "truenas/rhoai-models/${V2_MODEL_PREFIX}/model.joblib"

V1_SOURCE_SHA256="$(mc cat "$V1_KFP_ARTIFACT" | sha256sum | awk '{print $1}')"
V2_SOURCE_SHA256="$(mc cat "$V2_KFP_ARTIFACT" | sha256sum | awk '{print $1}')"
V1_SHA256="$(
  mc cat "truenas/rhoai-models/${V1_MODEL_PREFIX}/model.joblib" |
    sha256sum | awk '{print $1}'
)"
V2_SHA256="$(
  mc cat "truenas/rhoai-models/${V2_MODEL_PREFIX}/model.joblib" |
    sha256sum | awk '{print $1}'
)"

test "$V1_SOURCE_SHA256" = "$V1_SHA256"
test "$V2_SOURCE_SHA256" = "$V2_SHA256"
test "$V1_SHA256" != "$V2_SHA256"
printf 'v1 sha256=%s\nv2 sha256=%s\n' "$V1_SHA256" "$V2_SHA256"

cat > /tmp/day8-lineage.env <<EOF
V1_RUN_NAME=${V1_RUN_NAME}
V1_RUN_ID=${V1_RUN_ID}
V1_KFP_ARTIFACT=${V1_KFP_ARTIFACT}
V1_MODEL_PREFIX=${V1_MODEL_PREFIX}
V1_ACCURACY=${V1_ACCURACY}
V1_ROC_AUC=${V1_ROC_AUC}
V1_SHA256=${V1_SHA256}
V2_RUN_NAME=${V2_RUN_NAME}
V2_RUN_ID=${V2_RUN_ID}
V2_KFP_ARTIFACT=${V2_KFP_ARTIFACT}
V2_MODEL_PREFIX=${V2_MODEL_PREFIX}
V2_ACCURACY=${V2_ACCURACY}
V2_ROC_AUC=${V2_ROC_AUC}
V2_SHA256=${V2_SHA256}
EOF
```

`mc cp`는 모델을 재훈련하지 않고 Day7의 바이트를 그대로 승격한다. 같은 파일인지 여부는 `sha256`으로 검증한다.

### Model Registry 컴포넌트 확인
```bash
oc get dsc default-dsc \
  -o jsonpath='{.spec.components.modelregistry.managementState}{"\n"}'
oc get modelregistries.components.platform.opendatahub.io \
  default-modelregistry -o yaml
oc get crd modelregistries.modelregistry.opendatahub.io
```

`managementState`가 `Managed`이고 컴포넌트 상태가 `Ready`여야 한다.

### 실습용 Registry DB Secret 생성
RHOAI 3.4의 Model Registry CR은 MySQL 또는 PostgreSQL 구성이 필요하다. 이 실습에서는 Model Registry Operator가 생성하는 실습용 PostgreSQL을 사용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: jukebox-registry-db
  namespace: rhoai-model-registries
type: Opaque
stringData:
  database-password: "<MODEL_REGISTRY_DB_PW>"
EOF
```

### ModelRegistry 생성
이미 `jukebox-registry`가 `Available=True`이면 다시 만들지 않고 다음 절로 이동한다.

```bash
oc apply -f - <<'EOF'
apiVersion: modelregistry.opendatahub.io/v1beta1
kind: ModelRegistry
metadata:
  name: jukebox-registry
  namespace: rhoai-model-registries
spec:
  rest: {}
  postgres:
    generateDeployment: true
    database: model_registry
    username: <MODEL_REGISTRY_DB_ID>
    passwordSecret:
      name: jukebox-registry-db
      key: database-password
EOF

oc get modelregistries.modelregistry.opendatahub.io \
  jukebox-registry -n rhoai-model-registries -w
```

`AVAILABLE=True`가 되면 `Ctrl+C`로 종료한다.

### Registry REST endpoint 확인
Model Registry Operator는 Registry별 REST Service를 생성하지만 개별 Route를 자동 생성하지 않는다. API를 확인할 때는 Service를 port-forward한다.

```bash
oc get svc jukebox-registry -n rhoai-model-registries
oc port-forward -n rhoai-model-registries \
  svc/jukebox-registry 18080:8080
```

다른 터미널에서 확인한다.

```bash
curl -fsS \
  http://127.0.0.1:18080/api/model_registry/v1alpha3/registered_models |
  jq .
```

### Day7 baseline을 Registry v1로 등록
RHOAI 대시보드에서 다음 순서로 등록한다.

> 이 연속 실습에서 새로 사용하는 Registered Model 이름은 `fraud-kfp`다. 이전 Day8 자료로 만든 `fraud-detection`이 남아 있더라도 재사용하지 않는다. 두 모델의 v1/v2는 ID와 생명주기 상태가 서로 독립적이다.

1. `Settings` -> `Model resources and operations` -> `Model registry settings`에서 `jukebox-registry`가 표시되는지 확인한다.
2. `AI hub` -> `Models` -> `Registry`로 이동하고 `jukebox-registry`를 선택한다.
3. **Register model**을 누르고 **Model location and storage**에서 **Register**를 선택한다. 이미 MinIO에 저장된 파일을 참조하므로 **Register and store**는 선택하지 않는다.
4. **Model details**를 입력한다.
   - **Model name**: `fraud-kfp`
   - **Model description**: `Day 7 KFP RandomForest lineage`
5. **Version details**를 입력한다.
   - **Version name**: `v1`
   - **Source model format**: `scikit-learn`
   - **Source model format version**: `1.6.1`
6. **Model location**에서 **Object storage**를 선택한다.
   - **Project**: `jukebox`
   - **Connection name**: `TrueNAS S3 models` (`aws-connection-models`)
   - **Path**: 앞에서 출력한 `${V1_MODEL_PREFIX}/model.joblib`
7. 다음 custom property를 추가한다.
   - `algorithm=RandomForestClassifier`
   - `n_estimators=20`
   - `random_state=42`
   - `kfp_run_name=<V1_RUN_NAME 값>`
   - `kfp_run_id=<V1_RUN_ID 값>`
   - `accuracy=<V1_ACCURACY 값>`
   - `roc_auc=<V1_ROC_AUC 값>`
   - `sha256=<V1_SHA256 값>`
   - `stage=Production`
8. 등록 후 v1 모델 위치가 `s3://rhoai-models/${V1_MODEL_PREFIX}/model.joblib`인지 확인한다.

터미널 값을 다시 출력할 수 있다.

```bash
source /tmp/day8-lineage.env
printf 'Path=%s/model.joblib\n' "$V1_MODEL_PREFIX"
printf 'Run=%s (%s)\naccuracy=%s roc_auc=%s\nsha256=%s\n' \
  "$V1_RUN_NAME" "$V1_RUN_ID" \
  "$V1_ACCURACY" "$V1_ROC_AUC" "$V1_SHA256"
```

### Day7 candidate를 Registry v2로 등록
1. `fraud-kfp` Registered Model 상세 화면에서 새 Model Version을 추가한다.
2. **Version name**은 `v2`, 모델 형식은 `scikit-learn`, 형식 버전은 `1.6.1`로 입력한다.
3. `TrueNAS S3 models` Connection을 선택하고 **Path**에 `${V2_MODEL_PREFIX}/model.joblib`을 입력한다.
4. 다음 custom property를 추가한다.
   - `algorithm=RandomForestClassifier`
   - `n_estimators=200`
   - `random_state=42`
   - `kfp_run_name=<V2_RUN_NAME 값>`
   - `kfp_run_id=<V2_RUN_ID 값>`
   - `accuracy=<V2_ACCURACY 값>`
   - `roc_auc=<V2_ROC_AUC 값>`
   - `sha256=<V2_SHA256 값>`
   - `stage=Staging`
5. 등록 후 v2 모델 위치가 `s3://rhoai-models/${V2_MODEL_PREFIX}/model.joblib`인지 확인한다.

```bash
source /tmp/day8-lineage.env
printf 'Path=%s/model.joblib\n' "$V2_MODEL_PREFIX"
printf 'Run=%s (%s)\naccuracy=%s roc_auc=%s\nsha256=%s\n' \
  "$V2_RUN_NAME" "$V2_RUN_ID" \
  "$V2_ACCURACY" "$V2_ROC_AUC" "$V2_SHA256"
```

### Registry ID 확인
Registry `port-forward`를 유지하고 다른 터미널에서 실행한다.

```bash
REGISTERED_MODEL_ID="$(
  curl -fsS \
    http://127.0.0.1:18080/api/model_registry/v1alpha3/registered_models |
    jq -r '.items[] | select(.name == "fraud-kfp") | .id'
)"

V1_MODEL_VERSION_ID="$(
  curl -fsS \
    http://127.0.0.1:18080/api/model_registry/v1alpha3/model_versions |
    jq -r --arg id "$REGISTERED_MODEL_ID" \
      '.items[] | select(.registeredModelId == $id and .name == "v1") | .id'
)"

V2_MODEL_VERSION_ID="$(
  curl -fsS \
    http://127.0.0.1:18080/api/model_registry/v1alpha3/model_versions |
    jq -r --arg id "$REGISTERED_MODEL_ID" \
      '.items[] | select(.registeredModelId == $id and .name == "v2") | .id'
)"

test -n "$REGISTERED_MODEL_ID"
test -n "$V1_MODEL_VERSION_ID"
test -n "$V2_MODEL_VERSION_ID"

printf 'Registered Model ID=%s\nv1 Version ID=%s\nv2 Version ID=%s\n' \
  "$REGISTERED_MODEL_ID" "$V1_MODEL_VERSION_ID" "$V2_MODEL_VERSION_ID"

cat >> /tmp/day8-lineage.env <<EOF
REGISTERED_MODEL_ID=${REGISTERED_MODEL_ID}
V1_MODEL_VERSION_ID=${V1_MODEL_VERSION_ID}
V2_MODEL_VERSION_ID=${V2_MODEL_VERSION_ID}
EOF
```

ID는 클러스터마다 달라지므로 문서나 정적 YAML에 숫자로 고정하지 않는다.

### v1/v2 InferenceService 배포
Day10에서 두 버전을 동시에 Route backend로 사용하므로 별도의 InferenceService로 배포한다.

먼저 `kserve-sa`가 모델 S3 Connection Secret을 참조하는지 확인한다. Secret 참조는 InferenceService를 생성하기 전에 존재해야 storage initializer에 S3 인증정보가 주입된다.

```bash
oc get secret aws-connection-models -n jukebox

if ! oc get sa kserve-sa -n jukebox \
  -o jsonpath='{.secrets[*].name}' | grep -qw aws-connection-models; then
  oc patch sa kserve-sa -n jukebox --type=merge \
    -p '{"secrets":[{"name":"aws-connection-models"}]}'
fi

oc get sa kserve-sa -n jukebox \
  -o jsonpath='{.secrets[*].name}{"\n"}'
```

마지막 출력에 `aws-connection-models`가 있어야 한다. 이 참조를 나중에 추가했다면 기존 InferenceService를 삭제 후 다시 생성해야 한다.

```bash
source /tmp/day8-lineage.env

cat <<EOF | oc apply -f -
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-kfp-v1
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
    model-version: v1
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
    modelregistry.opendatahub.io/registered-model-id: "${REGISTERED_MODEL_ID}"
    modelregistry.opendatahub.io/model-version-id: "${V1_MODEL_VERSION_ID}"
spec:
  predictor:
    serviceAccountName: kserve-sa
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
        version: "1"
      runtime: mlserver-sklearn
      storageUri: s3://rhoai-models/${V1_MODEL_PREFIX}
      env:
        - name: MLSERVER_MODEL_NAME
          value: fraud
      readinessProbe:
        httpGet:
          path: /v2/models/fraud/ready
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 5
        timeoutSeconds: 5
      livenessProbe:
        httpGet:
          path: /v2/models/fraud/ready
          port: 8080
        initialDelaySeconds: 20
        periodSeconds: 10
        timeoutSeconds: 5
---
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-kfp-v2
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
    model-version: v2
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
    modelregistry.opendatahub.io/registered-model-id: "${REGISTERED_MODEL_ID}"
    modelregistry.opendatahub.io/model-version-id: "${V2_MODEL_VERSION_ID}"
spec:
  predictor:
    serviceAccountName: kserve-sa
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
        version: "1"
      runtime: mlserver-sklearn
      storageUri: s3://rhoai-models/${V2_MODEL_PREFIX}
      env:
        - name: MLSERVER_MODEL_NAME
          value: fraud
      readinessProbe:
        httpGet:
          path: /v2/models/fraud/ready
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 5
        timeoutSeconds: 5
      livenessProbe:
        httpGet:
          path: /v2/models/fraud/ready
          port: 8080
        initialDelaySeconds: 20
        periodSeconds: 10
        timeoutSeconds: 5
EOF

oc wait --for=condition=Ready isvc/fraud-kfp-v1 \
  -n jukebox --timeout=300s
oc wait --for=condition=Ready isvc/fraud-kfp-v2 \
  -n jukebox --timeout=300s

oc get isvc fraud-kfp-v1 fraud-kfp-v2 -n jukebox
```

`MLSERVER_MODEL_NAME=fraud`를 사용하므로 두 backend 모두 같은 `/v2/models/fraud/infer` URL을 제공한다.

### v1/v2 직접 추론 검증
두 RandomForest 모델의 차이를 관찰할 수 있는 요청을 만든다. 검증한 데이터셋과 `random_state=42` 기준으로 v1은 `1`, v2는 `0`을 반환한다. 패키지 버전이 달라 결과가 바뀌더라도 두 endpoint가 정상 응답하고 Registry·S3 lineage가 일치하는지가 우선 기준이다.

```bash
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

oc port-forward -n jukebox \
  deploy/fraud-kfp-v1-predictor 18081:8080 >/tmp/fraud-kfp-v1-pf.log 2>&1 &
V1_PF=$!
oc port-forward -n jukebox \
  deploy/fraud-kfp-v2-predictor 18082:8080 >/tmp/fraud-kfp-v2-pf.log 2>&1 &
V2_PF=$!
sleep 3

curl -fsS -H 'Content-Type: application/json' \
  http://127.0.0.1:18081/v2/models/fraud/infer \
  -d @/tmp/python3/fraud-kfp-request.json | tee /tmp/day8-v1-response.json | jq .

curl -fsS -H 'Content-Type: application/json' \
  http://127.0.0.1:18082/v2/models/fraud/infer \
  -d @/tmp/python3/fraud-kfp-request.json | tee /tmp/day8-v2-response.json | jq .

printf 'v1 prediction=%s\nv2 prediction=%s\n' \
  "$(jq -r '.outputs[0].data[0]' /tmp/day8-v1-response.json)" \
  "$(jq -r '.outputs[0].data[0]' /tmp/day8-v2-response.json)"

kill "$V1_PF" "$V2_PF"
wait "$V1_PF" "$V2_PF" 2>/dev/null || true
```

### v2 승격
직접 추론과 metadata를 확인한 뒤 v2의 `stage`를 `Staging`에서 `Production`으로 변경한다. Day10의 점진적 전환이 끝날 때까지 v1도 `Production`으로 유지한다.

확인 항목은 다음과 같다.

1. v1/v2의 `kfp_run_id`가 서로 다르다.
2. Registry의 S3 URI와 각 InferenceService `storageUri`가 같은 prefix를 가리킨다.
3. Registry의 `sha256`과 승격한 S3 객체의 해시가 같다.
4. v2가 직접 추론에 성공한 후에만 `stage=Production`으로 변경한다.
5. Day10 전환 완료 후 v1을 `stage=Archived`로 변경한다.

> Registry 기본 필드 `state=LIVE`는 객체 생명주기이고 `stage=Staging/Production/Archived`는 이 커리큘럼의 배포 승인 custom property다. v2를 승격해도 v1 stage는 자동으로 변경되지 않는다.

### Day10 인계 상태 확인
```bash
source /tmp/day8-lineage.env

oc get isvc fraud-kfp-v1 fraud-kfp-v2 -n jukebox

for name in fraud-kfp-v1 fraud-kfp-v2; do
  oc get isvc "$name" -n jukebox \
    -o jsonpath='{.metadata.name}{" Ready="}{range .status.conditions[?(@.type=="Ready")]}{.status}{end}{" URI="}{.spec.predictor.model.storageUri}{"\n"}'
done

oc get isvc fraud-kfp-v1 -n jukebox \
  -o jsonpath='{.metadata.annotations.modelregistry\.opendatahub\.io/model-version-id}{"\n"}'
oc get isvc fraud-kfp-v2 -n jukebox \
  -o jsonpath='{.metadata.annotations.modelregistry\.opendatahub\.io/model-version-id}{"\n"}'
```

Day10이 이 두 InferenceService와 Registry 버전을 그대로 사용하므로 여기서는 삭제하지 않는다.
