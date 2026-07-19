# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 6 - Step 3 vLLM Tensor Parallel 2

> 사전 활성화: [Week6 Step 2](<Week6-Step2 TP1 기준선 실습.md>)의 TP1 요청 5회와 측정 파일 생성을 완료한다.

TP1 predictor를 제거해 GPU를 반환한 뒤 같은 모델을 `tensor_parallel_size=2`와 단일 노드 multiprocessing backend로 배포한다. 두 배포를 동시에 띄우지 않는다.

### TP1 GPU 반환

```bash
oc delete isvc week6-qwen-tp1 -n rhoai-tp-lab --ignore-not-found
oc wait --for=delete deployment/week6-qwen-tp1-predictor \
  -n rhoai-tp-lab --timeout=300s
oc delete servingruntime week6-vllm-tp1 \
  -n rhoai-tp-lab --ignore-not-found

oc get node ocp-w01-gpu \
  -o jsonpath='{.status.allocatable.nvidia\.com/gpu}{"\n"}'
```

allocatable은 `2`로 유지된다. 사용 중인 GPU는 Pod request로 확인하며 allocatable 값 자체에서 차감되어 보이지 않는다.

### TP2 ServingRuntime과 InferenceService

```bash
oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: week6-vllm-tp2
  namespace: rhoai-tp-lab
  annotations:
    opendatahub.io/recommended-accelerators: '["nvidia.com/gpu"]'
    opendatahub.io/runtime-version: v0.18.0
    openshift.io/display-name: Week 6 vLLM TP2
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
        - --distributed-executor-backend=mp
        - --tensor-parallel-size=2
      env:
        - name: HF_HOME
          value: /tmp/hf_home
        - name: NCCL_DEBUG
          value: INFO
        - name: NCCL_DEBUG_SUBSYS
          value: INIT,COLL
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
  name: week6-qwen-tp2
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
      runtime: week6-vllm-tp2
      storageUri: oci://192.168.10.50:5010/models/qwen2.5-0.5b-instruct:7ae5576
      volumeMounts:
        - name: dshm
          mountPath: /dev/shm
      resources:
        requests:
          cpu: "4"
          memory: 8Gi
          nvidia.com/gpu: "2"
        limits:
          cpu: "8"
          memory: 16Gi
          nvidia.com/gpu: "2"
EOF
```

### Ready와 rank 초기화 확인

```bash
oc wait --for=condition=Ready isvc/week6-qwen-tp2 \
  -n rhoai-tp-lab --timeout=900s

oc get isvc week6-qwen-tp2 -n rhoai-tp-lab -o json | \
  jq '{created:.metadata.creationTimestamp,
    ready:(.status.conditions[] | select(.type=="Ready") |
      {status,lastTransitionTime,reason})}' | \
  tee /tmp/week6-tp2-startup.json

TP2_POD=$(oc get pod -n rhoai-tp-lab \
  -l serving.kserve.io/inferenceservice=week6-qwen-tp2 \
  -o jsonpath='{.items[0].metadata.name}')

oc get pod "$TP2_POD" -n rhoai-tp-lab -o json | jq '{
  node:.spec.nodeName,
  gpuRequest:[.spec.containers[] |
    select(.name=="kserve-container") |
    .resources.requests["nvidia.com/gpu"]],
  gpuLimit:[.spec.containers[] |
    select(.name=="kserve-container") |
    .resources.limits["nvidia.com/gpu"]]
}'

oc logs "$TP2_POD" -n rhoai-tp-lab -c kserve-container | \
  grep -Ei 'tensor.parallel|world.?size|rank|multiprocess|NCCL' | \
  tee /tmp/week6-tp2-parallel.log
```

로그 표현은 vLLM 버전에 따라 다르지만 world size 또는 tensor parallel size가 `2`이고 rank 0/1 초기화 또는 NCCL communicator 초기화가 확인돼야 한다.

### 두 GPU process 확인

```bash
oc exec "$TP2_POD" -n rhoai-tp-lab -c kserve-container -- \
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu \
  --format=csv

oc exec "$TP2_POD" -n rhoai-tp-lab -c kserve-container -- \
  nvidia-smi pmon -c 1
```

GPU 0과 GPU 1 모두에 vLLM worker process와 GPU memory 사용량이 있어야 한다. 이것이 단순히 GPU 두 개를 Pod에 노출한 것과 실제 TP rank가 두 카드에서 동작하는 것을 구분하는 핵심 증거다.

### 동일 요청 5회 측정

```bash
bash <<'BASH'
set -euo pipefail

oc port-forward -n rhoai-tp-lab \
  deployment/week6-qwen-tp2-predictor 18093:8080 \
  > /tmp/week6-tp2-port-forward.log 2>&1 &
TP2_PF_PID=$!
trap 'kill "$TP2_PF_PID" 2>/dev/null || true' EXIT

TP2_MODELS=
for _ in $(seq 1 20); do
  if TP2_MODELS=$(curl --connect-timeout 2 --max-time 5 -fsS \
    http://127.0.0.1:18093/v1/models 2>/dev/null); then
    break
  fi

  if ! kill -0 "$TP2_PF_PID" 2>/dev/null; then
    cat /tmp/week6-tp2-port-forward.log >&2
    exit 1
  fi
  sleep 1
done

if [ -z "$TP2_MODELS" ]; then
  cat /tmp/week6-tp2-port-forward.log >&2
  echo 'ERROR: TP2 vLLM API가 준비되지 않았습니다.' >&2
  exit 1
fi

TP2_MODEL=$(jq -r '.data[0].id // empty' <<<"$TP2_MODELS")
if [ -z "$TP2_MODEL" ]; then
  echo 'ERROR: /v1/models 응답에서 model ID를 찾지 못했습니다.' >&2
  exit 1
fi

cat > /tmp/week6-chat-request.json <<EOF
{"model":"$TP2_MODEL","messages":[{"role":"user","content":"OpenShift AI에서 GPU Pod가 Pending일 때 첫 세 가지 점검 항목을 말해 주세요."}],"max_tokens":64,"temperature":0}
EOF

printf 'run\ttime_starttransfer\ttime_total\n' \
  > /tmp/week6-tp2-times.tsv

for N in 1 2 3 4 5; do
  curl -fsS -o "/tmp/week6-tp2-response-${N}.json" \
    -w "${N}\t%{time_starttransfer}\t%{time_total}\n" \
    -H 'Content-Type: application/json' \
    http://127.0.0.1:18093/v1/chat/completions \
    -d @/tmp/week6-chat-request.json | \
    tee -a /tmp/week6-tp2-times.tsv
done

jq '{model,answer:.choices[0].message.content,usage}' \
  /tmp/week6-tp2-response-5.json
cat /tmp/week6-tp2-times.tsv

kill "$TP2_PF_PID" 2>/dev/null || true
wait "$TP2_PF_PID" 2>/dev/null || true
trap - EXIT
BASH
```

첫 요청은 CUDA graph, cache와 kernel 준비 때문에 뒤의 요청보다 느릴 수 있다. 비교표에는 첫 요청과 warm 요청 2~5를 구분해 기록한다.

### PCIe/NCCL 문제 판정

Ready가 되지 않으면 다음을 먼저 확인한다.

```bash
oc describe pod "$TP2_POD" -n rhoai-tp-lab
oc logs "$TP2_POD" -n rhoai-tp-lab --all-containers
oc get events -n rhoai-tp-lab --sort-by=.lastTimestamp | tail -40
```

`peer access`, custom all-reduce 또는 NCCL P2P 오류로만 실패하면 TP2 heredoc의 runtime `args`에 `--disable-custom-all-reduce`, `env`에 `NCCL_P2P_DISABLE=1`을 추가해 삭제 후 재배포한다. 이 fallback은 host shared-memory/PCIe 경로로 기능을 검증하지만 효율적인 GPU P2P 통신을 입증하지는 않는다. 처음부터 fallback을 켜지 말고 기본 transport 결과를 먼저 기록한다.

### 확인 기준

- predictor request와 limit이 모두 `nvidia.com/gpu=2`다.
- rank/world size 2 또는 NCCL communicator 2-rank 초기화가 로그에 있다.
- 두 GPU 모두 vLLM process와 memory 사용량을 표시한다.
- 다섯 API 요청이 성공하고 측정 파일이 생성됐다.
- port-forward process가 종료됐다.
