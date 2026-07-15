# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day8

> 사전 활성화: [Week1 Day1&2 - AI Pipelines와 Model Registry 구성](Week1-Day1%262-환경구성.md#ai-pipelines와-model-registry-구성)과 [KServe RawDeployment 구성](Week1-Day1%262-환경구성.md#kserve-rawdeployment-구성)을 먼저 확인한다.

Model Registry에 모델과 버전을 등록하고, 메타데이터로 승격 상태를 관리한 뒤 KServe RawDeployment와 연결한다.

> Model Registry는 모델 파일 자체가 아니라 모델 이름, 버전, 성능, 저장 위치 같은 메타데이터를 관리한다. 실제 모델 파일은 MinIO S3에 유지한다.

### Model Registry 컴포넌트 확인
```bash
oc get dsc default-dsc \
  -o jsonpath='{.spec.components.modelregistry.managementState}{"\n"}'
oc get modelregistries.components.platform.opendatahub.io default-modelregistry -o yaml
oc get crd modelregistries.modelregistry.opendatahub.io
```

`managementState`가 `Managed`이고 컴포넌트 상태가 `Ready`여야 한다.

### 실습용 Registry DB Secret 생성
RHOAI 3.4의 Model Registry CR은 MySQL 또는 PostgreSQL 구성이 필요하다. 이 실습에서는 Model Registry Operator가 생성하는 테스트용 PostgreSQL을 사용한다.

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

`PHASE`가 `Ready`가 되면 `Ctrl+C`로 종료한다.

```bash
oc get pods,svc,route,pvc -n rhoai-model-registries
oc get modelregistries.modelregistry.opendatahub.io \
  jukebox-registry -n rhoai-model-registries -o yaml
```

### Registry REST endpoint 확인
Model Registry Operator는 Registry별 REST Service를 생성하지만 개별 Route를 자동 생성하지 않는다. 대시보드에서 등록하거나, API를 직접 확인할 때는 Service를 port-forward한다.

```bash
oc get svc jukebox-registry -n rhoai-model-registries
oc port-forward -n rhoai-model-registries svc/jukebox-registry 18080:8080
```

다른 터미널에서 API 응답을 확인한다.

```bash
curl -s http://127.0.0.1:18080/api/model_registry/v1alpha3/registered_models | jq .
```

### 모델 v1 등록
RHOAI 대시보드에서 다음 순서로 등록한다.

1. `Settings` -> `Model resources and operations` -> `Model registry settings`에서 `jukebox-registry`가 목록에 표시되는지 확인한다.
2. `AI hub` -> `Models` -> `Registry`로 이동하고, **Model registry** 목록에서 `jukebox-registry`를 선택한다.
3. **Register model**을 누르고 **Model location and storage**에서 **Register**를 선택한다. 이미 MinIO에 저장된 모델의 위치와 메타데이터만 등록하며, **Register and store**는 선택하지 않는다.
4. **Model details**를 다음과 같이 입력한다.
   - **Model name**: `fraud-detection`
   - **Model description**: `Day 5 fraud detection model` 또는 실습 목적에 맞는 설명
5. **Version details**를 다음과 같이 입력한다.
   - **Version name**: `v1`
   - **Source model format**: `scikit-learn`
   - **Source model format version**: `1.6.1`
6. **Model location**에서 **Object storage**를 선택하고 다음과 같이 입력한다.
   - **Autofill from connection**을 누른다.
   - **Project**: `jukebox`
   - **Connection name**: `TrueNAS S3 models` (Kubernetes Secret 이름: `aws-connection-models`)
   - **Autofill**을 누른 뒤 Endpoint, Bucket, Region이 채워졌는지 확인한다.
   - **Path**: `fraud/model.joblib`
7. **Register model**을 누른다.
8. 생성된 `fraud-detection`의 `v1` 상세 화면에서 모델 위치가 `s3://rhoai-models/fraud/model.joblib`을 가리키는지 확인한다.
9. **Properties**에서 다음 custom property를 추가한다. `<DAY5_ROC_AUC>`는 자리표시자이므로 그대로 입력하지 않고, Day5 모델 생성 시 출력된 실제 값으로 바꾼다.
   - `algorithm=GradientBoostingClassifier`
   - `roc_auc=<DAY5_ROC_AUC>`
   - `random_state=42`
   - `stage=Staging`

Day5의 출력값을 기록하지 않았다면 Workbench 터미널에서 학습 스크립트를 다시 실행한다.

```bash
cd /tmp/python3
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=-1 python3 models/train_fraud_sklearn.py
```

출력된 `ROC-AUC = 0.xxx`의 숫자를 `roc_auc` property에 **Number** 타입으로 입력한다. 예를 들어 `ROC-AUC = 0.708`이라면 `<DAY5_ROC_AUC>` 대신 `0.708`을 입력한다. 학습 스크립트는 `random_state=42`를 사용하므로 동일한 데이터와 패키지 버전에서는 같은 결과를 생성한다.

  ### Registry 메타데이터 확인
앞에서 실행한 Registry `port-forward`를 유지하고 다른 Bastion 터미널에서 Registered Model ID와 v1 Model Version ID를 조회한다.

```bash
REGISTERED_MODEL_ID="$(
  curl -s http://127.0.0.1:18080/api/model_registry/v1alpha3/registered_models |
    jq -r '.items[] | select(.name == "fraud-detection") | .id'
)"

V1_MODEL_VERSION_ID="$(
  curl -s http://127.0.0.1:18080/api/model_registry/v1alpha3/model_versions |
    jq -r --arg id "$REGISTERED_MODEL_ID" \
      '.items[] | select(.registeredModelId == $id and .name == "v1") | .id'
)"

printf 'Registered Model ID=%s\nv1 Model Version ID=%s\n' \
  "$REGISTERED_MODEL_ID" "$V1_MODEL_VERSION_ID"
```

두 값이 모두 출력되는지 확인한다. ID는 클러스터마다 달라지므로 문서나 YAML에 고정하지 않는다.

### v1 Registry 모델 배포 및 기준 추론
Registry의 v1 메타데이터와 실제 S3 URI를 연결한 InferenceService를 생성한다. 실제 모델 로딩에는 `storageUri`가 사용되고, annotation은 배포가 어떤 Registry 모델과 버전을 참조했는지 추적하기 위한 메타데이터다.

```bash
cat <<EOF | oc apply -f -
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-registry-production
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
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
      storageUri: s3://rhoai-models/fraud
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

oc wait --for=condition=Ready \
  isvc/fraud-registry-production -n jukebox --timeout=300s
oc get isvc fraud-registry-production -n jukebox
```

`MLSERVER_MODEL_NAME=fraud`를 사용하므로 probe도 `/v2/models/fraud/ready`를 호출해야 한다. probe를 생략하면 KServe가 InferenceService 이름을 사용한 `/v2/models/fraud-registry-production/ready`를 생성하며, MLServer에는 해당 모델명이 없어 HTTP 404로 `READY=False`가 된다.

InferenceService를 port-forward한다.

```bash
oc port-forward -n jukebox \
  deploy/fraud-registry-production-predictor 18088:8080
```

다른 Bastion 터미널에서 Day5의 요청 파일로 v1을 호출한다.

```bash
curl -s -H 'Content-Type: application/json' \
  http://127.0.0.1:18088/v2/models/fraud/infer \
  -d @/tmp/python3/fraud-request.json | jq .
```

응답의 `outputs[0].data[0]`을 v1 기준값으로 기록한다. Day5 실습 데이터와 모델을 그대로 사용했다면 v1은 `0`을 반환한다. 정상 응답을 확인한 뒤 대시보드의 v1 상세 화면에서 `stage`를 `Staging`에서 `Production`으로 변경한다.

### 모델 v2 등록
1. `fraud-detection` Registered Model 상세 화면에서 새 Model Version을 추가한다.
2. **Version name**은 `v2`, **Source model format**은 `scikit-learn`, **Source model format version**은 `1.6.1`로 입력한다.
3. **Model location**에서 **Object storage**를 선택하고 `TrueNAS S3 models` Connection으로 자동 입력한 뒤 **Path**에 `fraud-v2/model.joblib`을 입력한다.
4. 다음 custom property를 추가하고 등록한다.
   - `algorithm=DummyClassifier`
   - `roc_auc=0.500`
   - `stage=Staging`

> Day5의 `train_fraud_sklearn_v2.py`는 Blue/Green 응답 차이를 명확하게 보여주기 위해 항상 `1`을 예측하는 `DummyClassifier`를 생성한다. 따라서 이 실습의 v2 승격은 Registry 상태 변경 절차를 익히기 위한 것이며, 실제 운영의 성능 기반 승격 사례가 아니다. 실제 운영에서는 v1보다 ROC-AUC가 낮은 이 모델을 Production으로 승격하면 안 된다.

### v2 Staging 추론 검증
Registry `port-forward`가 실행 중인 터미널은 유지한다. ID를 조회했던 Bastion 터미널에서 v2 Model Version ID를 조회한다.

```bash
V2_MODEL_VERSION_ID="$(
  curl -s http://127.0.0.1:18080/api/model_registry/v1alpha3/model_versions |
    jq -r --arg id "$REGISTERED_MODEL_ID" \
      '.items[] | select(.registeredModelId == $id and .name == "v2") | .id'
)"

printf 'v2 Model Version ID=%s\n' "$V2_MODEL_VERSION_ID"
```

v1 검증용 InferenceService를 삭제하고 같은 이름으로 v2를 배포한다. 이 실습 서비스에는 외부 Route가 연결되어 있지 않으므로 내부 검증 중에만 교체한다. 실제 운영 서비스의 버전 전환에는 Day5의 Blue/Green 또는 Canary 방식을 사용한다.

```bash
oc delete isvc fraud-registry-production -n jukebox --wait=true

cat <<EOF | oc apply -f -
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-registry-production
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
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
      storageUri: s3://rhoai-models/fraud-v2
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

oc wait --for=condition=Ready \
  isvc/fraud-registry-production -n jukebox --timeout=300s
```

다시 port-forward한 뒤 같은 요청을 호출한다.

```bash
oc port-forward -n jukebox \
  deploy/fraud-registry-production-predictor 18088:8080
```

다른 Bastion 터미널에서 실행한다.

```bash
curl -s -H 'Content-Type: application/json' \
  http://127.0.0.1:18088/v2/models/fraud/infer \
  -d @/tmp/python3/fraud-request.json | jq .
```

Day5의 v2 모델을 사용했다면 `outputs[0].data[0]`이 `1`로 반환된다. v1의 기준 응답 `0`과 v2의 응답 `1`을 비교하고, v2의 `storageUri`와 Model Version ID가 Registry 정보와 일치하는지 확인한다.

### v2 승격
1. v2 추론이 정상임을 확인한 뒤 v2의 `stage` custom property를 `Staging`에서 `Production`으로 변경한다.
2. v1의 `stage` custom property를 `Production`에서 `Archived`로 변경한다.
3. v2 상세 화면의 모델 위치 `s3://rhoai-models/fraud-v2/model.joblib`과 InferenceService의 `storageUri` `s3://rhoai-models/fraud-v2`가 일치하는지 확인한다.

> Model Registry API의 기본 `state` 값은 구현 버전에 따라 `LIVE`/`ARCHIVED`를 사용한다. 커리큘럼의 `Staging`/`Production`은 별도의 custom property로 기록해 배포 승인 단계를 표현한다.
> v2를 배포하더라도 v1이 자동으로 `ARCHIVED` 로 변경되지는 않으니 v2가 `Production` 로 승격 후 v1를 보관 처리 하기로 결정 시 직접 수정해야 한다.

REST API로 자동화할 수도 있지만 이 실습에서는 대시보드를 사용한다. RHOAI 3.4 Registry REST 서버는 `/openapi.json`을 제공하지 않으므로, API 자동화 코드는 설치 버전의 Model Registry API/SDK와 맞춰 작성해야 한다.
