# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 6 - Step 2 vLLM TP1 기준선

> 사전 활성화: [Week6 Step 1](<Week6-Step1 리소스 프로파일 실습.md>)의 request 여유와 OCI pull Secret을 확인한다.

같은 Qwen2.5 0.5B ModelCar를 GPU 한 장으로 먼저 배포한다. TP2 결과를 해석하려면 동일한 runtime image, 모델, context 길이와 요청으로 얻은 기준선이 필요하다.

### TP1 ServingRuntime과 InferenceService

```bash
oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: week6-vllm-tp1
  namespace: rhoai-tp-lab
  annotations:
    opendatahub.io/recommended-accelerators: '["nvidia.com/gpu"]'
    opendatahub.io/runtime-version: v0.18.0
    openshift.io/display-name: Week 6 vLLM TP1 baseline
spec:
  annotations:
    opendatahub.io/kserve-runtime: vllm
    prometheus.io/path: /metrics
    prometheus.io/port: "8080"
  containers:
    - name: kserve-container
      image: registry.redhat.io/rhaii/vllm-cuda-rhel9@sha256:ad06abf3bb5235ebb5b2df84cd1b9fd09e823f0ff2eebfc82bb4590275ccfe0b
      command: [python, -m, vllm.entrypoints.openai.api_server]
      args:
        - --port=8080
        - --model=/mnt/models
        - --served-model-name={{.Name}}
        - --max-model-len=2048
        - --max-num-seqs=4
        - --gpu-memory-utilization=0.50
      env:
        - name: HF_HOME
          value: /tmp/hf_home
      ports:
        - containerPort: 8080
          protocol: TCP
  multiModel: false
  supportedModelFormats:
    - name: vLLM
      autoSelect: true
---
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: week6-qwen-tp1
  namespace: rhoai-tp-lab
  annotations:
    serving.kserve.io/deploymentMode: Standard
spec:
  predictor:
    imagePullSecrets:
      - name: week6-model-registry
    nodeSelector:
      lab-role: gpu
    volumes:
      - name: dshm
        emptyDir:
          medium: Memory
          sizeLimit: 4Gi
    model:
      modelFormat:
        name: vLLM
      name: ""
      runtime: week6-vllm-tp1
      storageUri: oci://192.168.10.50:5010/models/qwen2.5-0.5b-instruct:7ae5576
      volumeMounts:
        - name: dshm
          mountPath: /dev/shm
      resources:
        requests:
          cpu: "4"
          memory: 8Gi
          nvidia.com/gpu: "1"
        limits:
          cpu: "8"
          memory: 16Gi
          nvidia.com/gpu: "1"
EOF
```

ModelCar가 `/mnt/models`에 mount되고 vLLM이 `tensor_parallel_size=1` 기본값으로 시작한다.

### 준비 상태와 시작 시간

```bash
oc wait --for=condition=Ready isvc/week6-qwen-tp1 \
  -n rhoai-tp-lab --timeout=600s

oc get isvc week6-qwen-tp1 -n rhoai-tp-lab -o json | \
  jq '{created:.metadata.creationTimestamp,
    ready:(.status.conditions[] | select(.type=="Ready") |
      {status,lastTransitionTime,reason})}' | \
  tee /tmp/week6-tp1-startup.json

TP1_POD=$(oc get pod -n rhoai-tp-lab \
  -l serving.kserve.io/inferenceservice=week6-qwen-tp1 \
  -o jsonpath='{.items[0].metadata.name}')

oc get pod "$TP1_POD" -n rhoai-tp-lab -o wide
oc logs "$TP1_POD" -n rhoai-tp-lab -c kserve-container \
  | grep -Ei 'engine|cuda|model|cache' | tail -30
```

### GPU 한 장 사용 확인

```bash
oc exec "$TP1_POD" -n rhoai-tp-lab -c kserve-container -- \
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu \
  --format=csv
```

Pod에는 GPU 한 장만 보이고 그 카드에 vLLM process가 있어야 한다.

### 동일 요청 5회 측정

같은 터미널에서 port-forward를 background로 실행하고 PID를 저장한다. 마지막에 반드시 종료한다.

```bash
bash <<'BASH'
set -euo pipefail

oc port-forward -n rhoai-tp-lab \
  deployment/week6-qwen-tp1-predictor 18092:8080 \
  > /tmp/week6-tp1-port-forward.log 2>&1 &
TP1_PF_PID=$!
trap 'kill "$TP1_PF_PID" 2>/dev/null || true' EXIT

TP1_MODELS=
for _ in $(seq 1 20); do
  if TP1_MODELS=$(curl --connect-timeout 2 --max-time 5 -fsS \
    http://127.0.0.1:18092/v1/models 2>/dev/null); then
    break
  fi

  if ! kill -0 "$TP1_PF_PID" 2>/dev/null; then
    cat /tmp/week6-tp1-port-forward.log >&2
    exit 1
  fi
  sleep 1
done

if [[ -z "$TP1_MODELS" ]]; then
  cat /tmp/week6-tp1-port-forward.log >&2
  echo 'ERROR: TP1 vLLM API가 준비되지 않았습니다.' >&2
  exit 1
fi

TP1_MODEL=$(jq -r '.data[0].id // empty' <<<"$TP1_MODELS")
if [[ -z "$TP1_MODEL" ]]; then
  echo 'ERROR: /v1/models 응답에서 model ID를 찾지 못했습니다.' >&2
  exit 1
fi

cat > /tmp/week6-chat-request.json <<EOF
{"model":"$TP1_MODEL","messages":[{"role":"user","content":"OpenShift AI에서 GPU Pod가 Pending일 때 첫 세 가지 점검 항목을 말해 주세요."}],"max_tokens":64,"temperature":0}
EOF

printf 'run\ttime_starttransfer\ttime_total\n' \
  > /tmp/week6-tp1-times.tsv

for N in 1 2 3 4 5; do
  curl -fsS -o "/tmp/week6-tp1-response-${N}.json" \
    -w "${N}\t%{time_starttransfer}\t%{time_total}\n" \
    -H 'Content-Type: application/json' \
    http://127.0.0.1:18092/v1/chat/completions \
    -d @/tmp/week6-chat-request.json | \
    tee -a /tmp/week6-tp1-times.tsv
done

jq '{model,answer:.choices[0].message.content,usage}' \
  /tmp/week6-tp1-response-5.json
cat /tmp/week6-tp1-times.tsv

kill "$TP1_PF_PID" 2>/dev/null || true
wait "$TP1_PF_PID" 2>/dev/null || true
trap - EXIT
BASH
```

첫 요청은 CUDA graph, cache와 kernel 준비 때문에 뒤의 요청보다 느릴 수 있다. 비교표에는 첫 요청과 warm 요청 2~5를 구분해 기록한다.

### 확인 기준

- `week6-qwen-tp1`이 Ready다.
- predictor가 GPU 하나를 요청하고 컨테이너에서도 GPU 하나만 보인다.
- 다섯 요청이 모두 HTTP 성공하고 응답 JSON에 `choices`와 `usage`가 있다.
- `/tmp/week6-tp1-startup.json`과 `/tmp/week6-tp1-times.tsv`가 생성됐다.
- port-forward process가 종료됐다.
