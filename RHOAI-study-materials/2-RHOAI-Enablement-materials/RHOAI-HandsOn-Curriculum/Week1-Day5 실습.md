# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 1 - Day5 - 

### 훈련 준비
```bash
ls /tmp/python3/models/train_fraud_sklearn.py
ls /tmp/python3/models/train_fraud_sklearn_v2.py
ls /tmp/python3/datasets/
```


### 모델 생성&배포
```bash
## 필요 라이브러리를 내부 넥서스에 업로드
cd /tmp
rm -rf /tmp/wheelhouse
mkdir -p /tmp/wheelhouse
cat >/tmp/day5-requirements.txt <<'EOF'
scikit-learn==1.6.1
pandas==2.3.3
numpy==1.26.4
scipy==1.13.1
joblib==1.4.2
threadpoolctl==3.5.0
python-dateutil==2.9.0.post0
pytz==2025.2
tzdata==2025.2
six==1.17.0
EOF

python3 -m venv /tmp/pypi-upload-venv
source /tmp/pypi-upload-venv/bin/activate
python3 -m pip install --upgrade pip

python3 -m pip download --only-binary=:all: -r /tmp/day5-requirements.txt -d /tmp/wheelhouse

python -m pip show twine pkginfo
## 설치 안됐으면 아래 진행
# python3 -m pip install \
#   'twine==5.0.0' \
#   'pkginfo==1.12.1.2'

twine upload \
  --repository-url http://192.168.10.50:8081/repository/pypi-hosted/ \
  -u <nexus_id> -p '<nexus_pw>' \
  /tmp/wheelhouse/*

## 내부 nexus 이용해서 모델 생성
cd /tmp/python3
python3 -m venv .venv
source .venv/bin/activate

python3 -m pip --isolated install \
  --index-url http://192.168.10.50:8081/repository/pypi-hosted/simple \
  --trusted-host 192.168.10.50 \
  -r /tmp/day5-requirements.txt

python3 -m pip check
## tensorflow 사용하는 python빌드는 vm 설정에 따라 지원여부 확인이 필요
CUDA_VISIBLE_DEVICES=-1 python3 models/train_fraud_sklearn.py
ls fraud/

mc alias set truenas http://192.168.20.5:9000 <minio_id> <minio_pw>
mc mb --ignore-existing truenas/rhoai-models
mc cp --recursive fraud/ truenas/rhoai-models/fraud/
mc ls truenas/rhoai-models/fraud/

CUDA_VISIBLE_DEVICES=-1 python3 models/train_fraud_sklearn_v2.py
ls fraud-v2/

mc mb --ignore-existing truenas/rhoai-models
mc cp --recursive fraud-v2/ truenas/rhoai-models/fraud-v2/
mc ls truenas/rhoai-models/fraud-v2/
```


### ServingRuntime 생성
```bash
oc get servingruntime -n jukebox
## mlserver-sklearn 없으면 아래 진행
# oc get template mlserver-runtime-template -n redhat-ods-applications -o jsonpath='{.objects[0].spec.containers[0].image}{"\n"}'

# oc apply -f <<'EOF'
# apiVersion: serving.kserve.io/v1alpha1
# kind: ServingRuntime
# metadata:
#   name: mlserver-sklearn
#   namespace: jukebox
#   labels:
#     opendatahub.io/dashboard: "true"
#   annotations:
#     openshift.io/display-name: "MLServer sklearn (RawDeployment)"
#     opendatahub.io/runtime-version: "1.7.1"
#     serving.kserve.io/server-type: mlserver
# spec:
#   annotations:
#     monitoring.opendatahub.io/scrape: "true"
#     opendatahub.io/kserve-runtime: mlserver
#     prometheus.io/path: /metrics
#     prometheus.io/port: "8082"
#   supportedModelFormats:
#     - name: sklearn
#       version: "1"
#       autoSelect: true
#   protocolVersions:
#     - v2
#   multiModel: false
#   containers:
#     - name: kserve-container
#       image: registry.redhat.io/rhoai/odh-mlserver-rhel9@sha256:d76bea18afe7b361847babb7a8ebc51fdbcd8164435f1bcb971e1701ba1bc595
#       env:
#         - name: MLSERVER_MODEL_IMPLEMENTATION
#           value: mlserver_sklearn.SKLearnModel
#         - name: MLSERVER_HTTP_PORT
#           value: "8080"
#         - name: MLSERVER_MODELS_DIR
#           value: /mnt/models
#       ports:
#         - containerPort: 8080
#           protocol: TCP
#       readinessProbe:
#         httpGet:
#           path: /v2/models/{{.Name}}/ready
#           port: 8080
#         initialDelaySeconds: 5
#         periodSeconds: 5
#         timeoutSeconds: 5
#         failureThreshold: 3
#       livenessProbe:
#         httpGet:
#           path: /v2/models/{{.Name}}/ready
#           port: 8080
#         initialDelaySeconds: 20
#         periodSeconds: 10
#         timeoutSeconds: 5
#         failureThreshold: 6
#       startupProbe:
#         exec:
#           command:
#             - /bin/sh
#             - -c
#             - |
#               [ -n "$(ls -A /mnt/models 2>/dev/null)" ]
#         initialDelaySeconds: 1
#         periodSeconds: 1
#         failureThreshold: 1
#       securityContext:
#         allowPrivilegeEscalation: false
#         capabilities:
#           drop:
#             - ALL
#         privileged: false
#         runAsNonRoot: true
#       resources:
#         requests:
#           cpu: "500m"
#           memory: 1Gi
#         limits:
#           cpu: "2"
#           memory: 2Gi
# EOF
```

### inferenceService 생성
```bash
oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-blue
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
    slot: blue
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
oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-green
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
    slot: green
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
```

### route 생성
```bash
oc apply -f - <<'EOF'
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: fraud-route
  namespace: jukebox
spec:
  to:
    kind: Service
    name: fraud-blue-predictor
    weight: 90
  alternateBackends:
    - kind: Service
      name: fraud-green-predictor
      weight: 10
  port:
    targetPort: http
  wildcardPolicy: None
EOF
```



### 모델 호출 테스트
```bash
# 1. Apply and wait.
oc wait --for=condition=Ready isvc/fraud-blue -n jukebox --timeout=300s
oc wait --for=condition=Ready isvc/fraud-green -n jukebox --timeout=300s

# 2. Create one fraud request body and reuse it for all route tests.
#    Feature order:
#      amount, age, tenure_months, num_claims, credit_score, distance_km, channel
cat > /tmp/python3/fraud-request.json <<'EOF'
{
  "inputs": [
    {
      "name": "predict",
      "shape": [1, 7],
      "datatype": "FP32",
      "data": [125.0, 42.0, 36.0, 1.0, 720.0, 12.5, 1.0]
    }
  ]
}
EOF

# 3. Route weight test. The inference URL stays the same because both
#    predictors serve the model as `fraud`; only the backend S3 prefix differs.

ROUTE=http://$(oc get route fraud-route -n jukebox -o jsonpath='{.spec.host}')

# patch 후 조금 기다렸다가 curl 수행. data[0] 값이 blue는 0, green은 1 이 나오는 것으로 route weight 결과 확인

# 90:10 blue/green
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"port":{"targetPort":"http"},"to":{"kind":"Service","name":"fraud-blue-predictor","weight":90},"alternateBackends":[{"kind":"Service","name":"fraud-green-predictor","weight":10}]}}'
for i in $(seq 1 20); do
  curl -s -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-request.json | jq -r '.outputs[0].data[0]'
done | sort | uniq -c

# 50:50 blue/green
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"port":{"targetPort":"http"},"to":{"kind":"Service","name":"fraud-blue-predictor","weight":50},"alternateBackends":[{"kind":"Service","name":"fraud-green-predictor","weight":50}]}}'
for i in $(seq 1 30); do
  curl -s -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-request.json | jq -r '.outputs[0].data[0]'
done | sort | uniq -c

# 10:90 blue/green
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"port":{"targetPort":"http"},"to":{"kind":"Service","name":"fraud-blue-predictor","weight":10},"alternateBackends":[{"kind":"Service","name":"fraud-green-predictor","weight":90}]}}'
for i in $(seq 1 20); do
  curl -s -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-request.json | jq -r '.outputs[0].data[0]'
done | sort | uniq -c

# Notes:
#   - If fraud and fraud-v2 contain the same model.joblib, both responses are
#     valid but indistinguishable from the response body.
#   - To observe different inference outputs, train fraud-v2 with a different
#     algorithm, seed, or hyperparameter, then upload it to
#     s3://rhoai-models/fraud-v2/model.joblib.
#   - For pure traffic-split verification, inspect predictor logs or route
#     metrics because the response model_name is intentionally the same: fraud.
```