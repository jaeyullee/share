# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 1 - Day4 - PyTorch

> 사전 활성화: [Week1 Day1&2 - KServe RawDeployment 구성](Week1-Day1%262-환경구성.md#kserve-rawdeployment-구성)을 먼저 확인한다.

PyTorch 로 훈련 후 ONNX 로 export 하여 OVMS 로 서빙한다.
jukebox 네임스페이스가 미리 준비된 전제로 진행한다.

### 훈련 준비
```bash
ls /tmp/python3/models/train_mnist_pytorch.py
ls /tmp/python3/datasets/_mnist_cache
```


### 모델 생성&배포
```bash
## 필요 라이브러리를 내부 넥서스에 업로드
cd /tmp
rm -rf /tmp/wheelhouse
mkdir -p /tmp/wheelhouse
cat >/tmp/day4-pytorch-requirements.txt <<'EOF'
torch==2.5.1+cpu
torchvision==0.20.1+cpu
onnx==1.17.0
numpy==1.26.4
pillow==11.3.0
filelock==3.16.1
typing-extensions==4.15.0
networkx==3.2.1
jinja2==3.1.6
MarkupSafe==3.0.2
fsspec==2024.12.0
sympy==1.13.1
mpmath==1.3.0
protobuf==3.20.3
EOF

python3 -m venv /tmp/pypi-upload-venv
source /tmp/pypi-upload-venv/bin/activate
python3 -m pip install --upgrade pip

python3 -m pip download --only-binary=:all: \
  -r /tmp/day4-pytorch-requirements.txt -d /tmp/wheelhouse \
  --index-url https://download.pytorch.org/whl/cpu \
  --extra-index-url https://pypi.org/simple

python -m pip show twine pkginfo
## 설치 안됐으면 아래 진행
# python3 -m pip install \
#   'twine==5.0.0' \
#   'pkginfo==1.12.1.2'

twine upload \
  --repository-url http://192.168.10.50:8081/repository/pypi-hosted/ \
  -u <NEXUS_ID> -p '<NEXUS_PW>' \
  /tmp/wheelhouse/*

## 내부 nexus 이용해서 모델 생성
cd /tmp/python3
python3 -m venv .venv
source .venv/bin/activate

python3 -m pip --isolated install \
  --index-url http://192.168.10.50:8081/repository/pypi-hosted/simple \
  --trusted-host 192.168.10.50 \
  -r /tmp/day4-pytorch-requirements.txt

python3 -m pip check
## tensorflow 사용하는 python빌드는 vm 설정에 따라 지원여부 확인이 필요
python3 models/train_mnist_pytorch.py
ls mnist/

mc alias set truenas http://192.168.20.5:9000 <MINIO_ID> <MINIO_PW>
mc mb --ignore-existing truenas/rhoai-models
mc cp --recursive mnist/ truenas/rhoai-models/mnist/
mc ls truenas/rhoai-models/mnist/
```


### ServingRuntime 생성
```bash
oc get servingruntime -n jukebox
## ovms-onnx 없으면 아래 진행
# oc get template kserve-ovms -n redhat-ods-applications -o jsonpath='{.objects[0].spec.containers[0].image}{"\n"}'

# oc apply -f - <<'EOF'
# apiVersion: serving.kserve.io/v1alpha1
# kind: ServingRuntime
# metadata:
#   name: ovms-onnx
#   namespace: jukebox
#   labels:
#     opendatahub.io/dashboard: "true"
#   annotations:
#     openshift.io/display-name: "OpenVINO Model Server (ONNX/TensorFlow)"
#     opendatahub.io/runtime-version: "v2026.1.0"
# spec:
#   annotations:
#     opendatahub.io/kserve-runtime: ovms
#     prometheus.io/path: /metrics
#     prometheus.io/port: "8888"
#   supportedModelFormats:
#     - name: onnx
#       version: "1"
#       autoSelect: true
#     - name: openvino_ir
#       version: opset13
#       autoSelect: true
#     - name: tensorflow
#       version: "1"
#       autoSelect: true
#     - name: tensorflow
#       version: "2"
#       autoSelect: true
#   protocolVersions:
#     - v2
#     - grpc-v2
#   multiModel: false
#   containers:
#     - name: kserve-container
#       image: registry.redhat.io/rhoai/odh-openvino-model-server-rhel9@sha256:1ab58519c50e2c3a9ebf0fee6d0708b1b5a0ae972aefcc722d87b2f62239a033
#       args:
#         - --model_name={{.Name}}
#         - --port=8001
#         - --rest_port=8888
#         - --model_path=/mnt/models
#         - --file_system_poll_wait_seconds=0
#         - --metrics_enable
#       ports:
#         - containerPort: 8888
#           protocol: TCP
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
  name: mnist-onnx
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    serviceAccountName: kserve-sa
    nodeSelector:
      lab-role: cpu
    minReplicas: 1
    model:
      modelFormat:
        name: onnx
        version: "1"
      runtime: ovms-onnx
      storageUri: s3://rhoai-models/mnist
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
oc wait --for=condition=Ready isvc/mnist-onnx -n jukebox --timeout=300s

# 2. Port-forward one predictor Deployment at a time.
#    The generated predictor Services are headless, so forward to Deployment
#    or Pod port 8080/8888 instead of service port 80.
oc port-forward -n jukebox deploy/mnist-onnx-predictor 18088:8888

# 3. Send a v2 request. Create the request body first.
#    train_mnist_pytorch.py also writes the same sample payload to
#    /tmp/python3/mnist-request.json when run from /tmp/python3.
cat > /tmp/python3/mnist-request.json <<EOF
{
  "inputs": [
    {
      "name": "input",
      "shape": [1, 1, 28, 28],
      "datatype": "FP32",
      "data": [$(python3 -c 'print(",".join(["0.0"] * 784))')]
    }
  ]
}
EOF

curl -s -H 'Content-Type: application/json' \
  http://127.0.0.1:18088/v2/models/mnist-onnx/infer \
  -d @/tmp/python3/mnist-request.json | jq .
```

### 실습 리소스 정리
InferenceService와 Predictor만 삭제하고 공유 `ovms-onnx` ServingRuntime은 유지한다.

```bash
oc delete isvc mnist-onnx -n jukebox \
  --ignore-not-found --wait=true --timeout=5m

# NotFound이면 삭제가 완료된 상태다.
oc get isvc mnist-onnx -n jukebox
oc get servingruntime ovms-onnx -n jukebox
```
