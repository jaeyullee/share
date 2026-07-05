# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 1 - Day3

### 네임스페이스 생성
```bash
oc apply -f <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: jukebox
  labels:
    opendatahub.io/dashboard: "true"
    modelmesh-enabled: "false"
EOF

```

### object storage 연결 준비
```bash
oc apply -f <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: aws-connection-models
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
    opendatahub.io/managed: "true"
  annotations:
    opendatahub.io/connection-type: s3
    openshift.io/display-name: models-minio
    # KServe S3 자격증명 힌트
    serving.kserve.io/s3-endpoint: 192.168.10.50:9000   # TrueNAS MinIO면 해당 endpoint로
    serving.kserve.io/s3-usehttps: "0"
    serving.kserve.io/s3-region: us-east-1
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: <minio_id>
  AWS_SECRET_ACCESS_KEY: <minio_pw>
  AWS_S3_ENDPOINT: http://192.168.10.50:9000
  AWS_DEFAULT_REGION: us-east-1
  AWS_S3_BUCKET: rhoai-models
EOF

oc apply -f <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kserve-sa
  namespace: jukebox
secrets:
  - name: aws-connection-models
EOF
```

### 이미지 준비
```bash
skopeo copy --dest-creds '<nexus_id>:<nexus_pw>' --dest-tls-verify=false docker://docker.io/seldonio/mlserver:1.6.1 docker://192.168.10.50:5010/seldonio/mlserver:1.6.1
```

### 모델 준비
```bash
mkdir -p /tmp/python3/models
cd /tmp/python3

cat <<'EOF' > models/train_iris_skleanr.py
#!/usr/bin/env python3
import json
import os
import joblib

OUTDIR = os.path.join(os.path.dirname(__file__), "iris")


def main():
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    X, y = load_iris(return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(Xtr, ytr)
    acc = accuracy_score(yte, clf.predict(Xte))
    print(f"accuracy = {acc:.3f}")

    os.makedirs(OUTDIR, exist_ok=True)
    joblib.dump(clf, os.path.join(OUTDIR, "model.joblib"))

    # MLServer v2 inference protocol 요청 예시
    req = {"inputs": [{"name": "input-0", "shape": [1, 4], "datatype": "FP32",
                       "data": Xte[0].tolist()}]}
    json.dump(req, open(os.path.join(OUTDIR, "sample_request.json"), "w"), indent=2)
    print(f"saved -> {OUTDIR}/model.joblib, sample_request.json")


if __name__ == "__main__":
    main()
EOF

## 필요 라이브러리를 내부 넥서스에 업로드
cd /tmp
rm -rf /tmp/wheelhouse
mkdir -p /tmp/wheelhouse
cat >/tmp/day3-iris-requirements.txt <<'EOF'
scikit-learn==1.6.1
numpy==1.26.4
scipy==1.13.1
joblib==1.4.2
threadpoolctl==3.5.0
EOF

python3 -m venv /tmp/pypi-upload-venv
source /tmp/pypi-upload-venv/bin/activate
python3 -m pip install --upgrade pip

python3 -m pip download --only-binary=:all: -r /tmp/day3-iris-requirements.txt -d /tmp/wheelhouse

python3 -m pip install \
  'twine==5.0.0' \
  'pkginfo==1.12.1.2'
python -m pip show twine pkginfo

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
  -r /tmp/day3-iris-requirements.txt

python3 -m pip check
python3 models/train_iris_sklearn.py
ls iris/

mc alias set truenas http://192.168.20.5:9000 <minio_id> <minio_pw>
mc mb --ignore-existing truenas/rhoai-models
mc cp iris/model.joblib truenas/rhoai-models/iris/model.joblib
mc ls truenas/rhoai-models/iris/
```

### ServingRuntime 생성
```bash
oc get template mlserver-runtime-template -n redhat-ods-applications -o jsonpath='{.objects[0].spec.containers[0].image}{"\n"}'

oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: mlserver-sklearn
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    openshift.io/display-name: "MLServer sklearn (RawDeployment)"
    opendatahub.io/runtime-version: "1.7.1"
    serving.kserve.io/server-type: mlserver
spec:
  annotations:
    monitoring.opendatahub.io/scrape: "true"
    opendatahub.io/kserve-runtime: mlserver
    prometheus.io/path: /metrics
    prometheus.io/port: "8082"
  supportedModelFormats:
    - name: sklearn
      version: "1"
      autoSelect: true
  protocolVersions:
    - v2
  multiModel: false
  containers:
    - name: kserve-container
      image: registry.redhat.io/rhoai/odh-mlserver-rhel9@sha256:d76bea18afe7b361847babb7a8ebc51fdbcd8164435f1bcb971e1701ba1bc595
      env:
        - name: MLSERVER_MODEL_IMPLEMENTATION
          value: mlserver_sklearn.SKLearnModel
        - name: MLSERVER_HTTP_PORT
          value: "8080"
        - name: MLSERVER_MODELS_DIR
          value: /mnt/models
      ports:
        - containerPort: 8080
          protocol: TCP
      readinessProbe:
        httpGet:
          path: /v2/models/{{.Name}}/ready
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 5
        timeoutSeconds: 5
        failureThreshold: 3
      livenessProbe:
        httpGet:
          path: /v2/models/{{.Name}}/ready
          port: 8080
        initialDelaySeconds: 20
        periodSeconds: 10
        timeoutSeconds: 5
        failureThreshold: 6
      startupProbe:
        exec:
          command:
            - /bin/sh
            - -c
            - |
              [ -n "$(ls -A /mnt/models 2>/dev/null)" ]
        initialDelaySeconds: 1
        periodSeconds: 1
        failureThreshold: 1
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop:
            - ALL
        privileged: false
        runAsNonRoot: true
      resources:
        requests:
          cpu: "500m"
          memory: 1Gi
        limits:
          cpu: "2"
          memory: 2Gi
EOF
```

### inferenceService 생성
```bash
oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: iris-sklearn
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
    serving.kserve.io/autoscalerClass: external
spec:
  predictor:
    serviceAccountName: kserve-sa
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
        version: "1"
      runtime: mlserver-sklearn
      storageUri: s3://rhoai-models/iris
      resources:
        requests:
          cpu: "500m"
          memory: 1Gi
        limits:
          cpu: "2"
          memory: 2Gi
EOF
```

### 추론 테스트
```bash
# 1. Wait until the InferenceService is ready.
oc get isvc iris-sklearn -n jukebox
oc wait --for=condition=Ready isvc/iris-sklearn -n jukebox --timeout=300s

# 2. Port-forward the RawDeployment predictor Deployment.
#    The generated predictor Service is headless, so forward to the Deployment
#    or Pod port 18080 instead of service port 80.
oc port-forward -n jukebox deploy/iris-sklearn-predictor 18088:8080

# 3. In another terminal, send a v2 inference request.
#    The input is one Iris flower sample:
#      [sepal length, sepal width, petal length, petal width]
#    The example [5.1, 3.5, 1.4, 0.2] is typically classified as setosa.
cat > /tmp/iris-request.json <<'EOF'
{
  "inputs": [
    {
      "name": "predict",
      "shape": [1, 4],
      "datatype": "FP64",
      "data": [5.1, 3.5, 1.4, 0.2]
    }
  ]
}
EOF

curl -s \
  -H 'Content-Type: application/json' \
  http://127.0.0.1:18088/v2/models/iris-sklearn/infer \
  -d @/tmp/iris-request.json | jq .
#
#    Response meaning:
#      model_name: model that handled the request
#      outputs[].shape: prediction result shape. [1] means one result for one sample.
#      outputs[].data: predicted Iris class id
#
#    Iris class id mapping:
#      0 = setosa
#      1 = versicolor
#      2 = virginica
#
#    If outputs[].data is [0], the model predicted "setosa" for the input sample.
#
# 4. Useful logs.
oc logs deploy/iris-sklearn-predictor -n jukebox -c storage-initializer
oc logs deploy/iris-sklearn-predictor -n jukebox -c kserve-container
#
# 5. Optional metrics check.
#    MLServer exposes inference API on 8080 and metrics on 8082. If 18088 is
#    forwarded to 8080, /metrics returns 404. Forward 8082 separately:
#    oc port-forward -n jukebox deploy/iris-sklearn-predictor 18082:8082
#
curl -s http://127.0.0.1:18082/metrics | grep -Ei 'request|infer|iris|mlserver'
```