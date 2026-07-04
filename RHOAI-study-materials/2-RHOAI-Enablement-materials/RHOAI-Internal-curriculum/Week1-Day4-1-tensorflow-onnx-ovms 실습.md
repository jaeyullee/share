# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 1 - Day4 - TensorFlow
TensorFlow 로 훈련 후 ONNX 로 export 하여 OVMS 로 서빙한다.
jukebox 네임스페이스가 미리 준비된 전제로 진행한다.

### 훈련 준비
```bash
ls /tmp/python3/models/train_jukebox_onnx.py
ls /tmp/python3/datasets/jukebox-spotify
```


### 모델 생성&배포
```bash
## 필요 라이브러리를 내부 넥서스에 업로드
cd /tmp
rm -rf /tmp/wheelhouse
mkdir -p /tmp/wheelhouse
cat >/tmp/day4-tensorflow-jukebox-requirements.txt <<'EOF'
tensorflow==2.15.1
tf2onnx==1.16.1
onnx==1.17.0
scikit-learn==1.6.1
pandas==2.3.3
numpy==1.26.4
protobuf==3.20.3
EOF

python3 -m venv /tmp/pypi-upload-venv
source /tmp/pypi-upload-venv/bin/activate
python3 -m pip install --upgrade pip

python3 -m pip download --only-binary=:all: -r /tmp/day4-tensorflow-jukebox-requirements.txt -d /tmp/wheelhouse

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
  -r /tmp/day4-tensorflow-jukebox-requirements.txt

python3 -m pip check
## tensorflow 사용하는 python빌드는 vm 설정에 따라 지원여부 확인이 필요
CUDA_VISIBLE_DEVICES=-1 python3 -c "import tensorflow as tf; print(tf.__version__)"
CUDA_VISIBLE_DEVICES=-1 python3 models/train_jukebox_onnx.py
ls jukebox/

mc alias set truenas http://192.168.20.5:9000 <minio_id> <minio_pw>
mc mb --ignore-existing truenas/rhoai-models
mc cp --recursive jukebox/ truenas/rhoai-models/jukebox/
mc ls truenas/rhoai-models/jukebox/
```


### ServingRuntime 생성
```bash
oc get template kserve-ovms -n redhat-ods-applications -o jsonpath='{.objects[0].spec.containers[0].image}{"\n"}'

oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: ovms-onnx
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    openshift.io/display-name: "OpenVINO Model Server (ONNX/TensorFlow)"
    opendatahub.io/runtime-version: "v2026.1.0"
spec:
  annotations:
    opendatahub.io/kserve-runtime: ovms
    prometheus.io/path: /metrics
    prometheus.io/port: "8888"
  supportedModelFormats:
    - name: onnx
      version: "1"
      autoSelect: true
    - name: openvino_ir
      version: opset13
      autoSelect: true
    - name: tensorflow
      version: "1"
      autoSelect: true
    - name: tensorflow
      version: "2"
      autoSelect: true
  protocolVersions:
    - v2
    - grpc-v2
  multiModel: false
  containers:
    - name: kserve-container
      image: registry.redhat.io/rhoai/odh-openvino-model-server-rhel9@sha256:1ab58519c50e2c3a9ebf0fee6d0708b1b5a0ae972aefcc722d87b2f62239a033
      args:
        - --model_name={{.Name}}
        - --port=8001
        - --rest_port=8888
        - --model_path=/mnt/models
        - --file_system_poll_wait_seconds=0
        - --metrics_enable
      ports:
        - containerPort: 8888
          protocol: TCP
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
파드가 배포되는 노드의 cpu타입에 따라 ovms프로세스가 cpu명령어 미지원으로 배포실패할 수 있음.
```bash
oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: jukebox-onnx
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    serviceAccountName: kserve-sa
    minReplicas: 1
    model:
      modelFormat:
        name: onnx
        version: "1"
      runtime: ovms-onnx
      storageUri: s3://rhoai-models/jukebox
      resources:
        requests:
          cpu: "500m"
          memory: 1Gi
        limits:
          cpu: "2"
          memory: 2Gi
EOF
```


### 모델 호출 테스트
```bash
# 1. Apply and wait.
oc wait --for=condition=Ready isvc/jukebox-onnx -n jukebox --timeout=300s

# 2. Port-forward one predictor Deployment at a time.
#    The generated predictor Services are headless, so forward to Deployment
#    or Pod port 8080/8888 instead of service port 80.
oc port-forward -n jukebox deploy/jukebox-onnx-predictor 18088:8888

# 3. Send a v2 request. Create the request body first.
#    train_jukebox_onnx.py also writes the same sample payload to
#    /tmp/python3/jukebox-request.json when run from /tmp/python3.
cat > /tmp/python3/jukebox-request.json <<'EOF'
{
  "inputs": [
    {
      "name": "input",
      "shape": [1, 13],
      "datatype": "FP32",
      "data": [
        0.0,
        0.33576908707618713,
        0.6529321670532227,
        0.974962592124939,
        0.7272727489471436,
        0.5815438628196716,
        0.0,
        0.20285813510417938,
        0.32361435890197754,
        0.2461814135313034,
        0.18625573813915253,
        0.5887918472290039,
        0.5969098806381226
      ]
    }
  ]
}
EOF

curl -s \
  -H 'Content-Type: application/json' \
  http://127.0.0.1:18088/v2/models/jukebox-onnx/infer \
  -d @/tmp/python3/mnist-request.json | jq .
```