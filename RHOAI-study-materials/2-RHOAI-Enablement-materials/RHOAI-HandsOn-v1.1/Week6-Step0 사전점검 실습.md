# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 6 - 2GPU Tensor Parallel 사전점검

> 사전 활성화: [Week3 Day11](<Week3-Day11 실습.md>)의 NFD/KMM/NVIDIA GPU Operator와 KServe Standard 구성을 완료한다. Week4 GPU 공유 설정을 적용한 상태라면 [Week4 Step 6](<Week4-Step6 실습.md>)에서 먼저 기본 exclusive GPU 상태로 복원한다.

같은 GPU worker에 RTX 5060 Ti 두 장을 노출하고 vLLM `tensor_parallel_size=2`를 검증한다. 이 실습은 **단일 노드 Tensor Parallel 기능 검증**이며, 여러 노드에 걸친 분산 추론이나 Ray, LeaderWorkerSet, `LLMInferenceService` 실습이 아니다.

### 실습 목적과 한계

Tensor Parallel은 한 레이어의 tensor 연산을 여러 GPU rank로 나누고 rank 사이에서 NCCL collective 통신을 수행한다. 이 실습에서는 다음을 입증한다.

1. 하나의 Pod가 물리 GPU 두 장을 exclusive resource로 할당받는다.
2. vLLM multiprocessing backend가 두 rank를 생성한다.
3. 두 GPU에 모델 프로세스가 올라가고 OpenAI 호환 API가 응답한다.
4. TP1과 TP2의 시작 시간, 지연과 GPU 메모리를 같은 모델로 비교한다.

Qwen2.5 0.5B는 한 장에도 충분히 들어가므로 TP2가 빨라질 필요는 없다. 두 5060 Ti 사이에는 NVLink가 없고 모델이 작아 통신 오버헤드 때문에 TP2가 더 느릴 수 있다. 이 결과는 실패가 아니라 TP 비용을 확인하는 관찰 항목이다.

고정한 모델 commit의 `config.json`은 `hidden_size=896`, attention head `14`, key/value head `2`다. 모두 TP size 2로 나눌 수 있어 모델 구조 자체가 TP2를 막지 않는다.

### 현재 리소스 계획

2026-07-16 점검값을 기준으로 한다.

| 항목 | GPU worker 현재값 | TP2 배포 후 계획 |
|---|---:|---:|
| VM | 14 vCPU / 32GiB RAM | 유지 |
| Kubernetes allocatable | 13.5 CPU / 약 29.2Gi / GPU 1 | CPU·메모리 유지 / GPU 2 |
| 기존 Pod request | 3.819 CPU / 8.953Gi | 동일 |
| TP2 predictor request | - | 4 CPU / 8Gi / GPU 2 |
| 예상 request 여유 | - | 약 5.68 CPU / 12.5Gi |

GPU memory는 각 카드 약 16GiB이며 두 장을 합친 32GiB가 하나의 일반 메모리 공간이 되는 것은 아니다. vLLM이 model tensor를 두 rank로 분할하고 GPU 간 통신으로 하나의 요청을 처리한다.

### 두 번째 GPU passthrough

Proxmox host에서 VM 102의 현재 설정과 사용하지 않는 두 번째 GPU를 다시 확인한다. 이 홈랩에서 두 번째 카드의 PCI function은 `02:00.0`과 `02:00.1`이고 같은 IOMMU group에 있다.

```bash
lspci -nnk -s 02:00.0
lspci -nnk -s 02:00.1
readlink /sys/bus/pci/devices/0000:02:00.0/iommu_group
readlink /sys/bus/pci/devices/0000:02:00.1/iommu_group
qm config 102 | grep -E '^(memory|cores|hostpci)'
```

두 function의 host driver가 `vfio-pci`이고 다른 VM이 사용하지 않는 것을 확인한 뒤 maintenance window에 연결한다. 첫 번째 GPU만 `x-vga=1`을 유지하고 두 번째에는 지정하지 않는다.

```bash
qm shutdown 102 --timeout 120
qm set 102 --hostpci1 02:00,pcie=1
qm start 102
```

클러스터에서 worker가 다시 Ready가 될 때까지 기다린다.

```bash
oc wait --for=condition=Ready node/ocp-w01-gpu --timeout=600s

oc debug node/ocp-w01-gpu -- chroot /host \
  lspci -nn | grep -i nvidia
```

VGA controller 두 개와 각 카드의 audio function 두 개가 보여야 한다. audio function을 별도 GPU로 세지 않는다.

### Device Plugin과 물리 GPU 확인

Week4에서 변경하는 공유 설정 하위 필드와 node label이 비어 있어야 한다.

```bash
oc get clusterpolicy gpu-cluster-policy -o json | \
  jq -c '.spec.devicePlugin.config // null'

oc get node ocp-w01-gpu -o json | \
  jq -r '.metadata.labels["nvidia.com/device-plugin.config"] // "__ABSENT__"'

oc get node ocp-w01-gpu \
  -o jsonpath='{.status.capacity.nvidia\.com/gpu}{"/"}{.status.allocatable.nvidia\.com/gpu}{"\n"}'

oc get node ocp-w01-gpu -o json | jq '{
  count:.metadata.labels["nvidia.com/gpu.count"],
  replicas:.metadata.labels["nvidia.com/gpu.replicas"],
  sharing:.metadata.labels["nvidia.com/gpu.sharing-strategy"],
  product:.metadata.labels["nvidia.com/gpu.product"]
}'
```

예상값은 `null`, `__ABSENT__`, `2/2`, `count=2`, `replicas=1`, `sharing=none`이다. `capacity=2`가 아니면 TP2를 시작하지 않는다. Time-Slicing으로 만든 논리 slot 두 개는 Tensor Parallel용 물리 GPU 두 장을 대체하지 못한다.

### 두 GPU를 한 Pod에 할당

검증용 Namespace와 Job을 만든다. 이 Job은 GPU 두 장을 동시에 요청하고 GPU 목록과 topology를 출력한다.

```bash
oc create namespace rhoai-tp-lab \
  --dry-run=client -o yaml | oc apply -f -

oc apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: week6-gpu-inventory
  namespace: rhoai-tp-lab
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      nodeSelector:
        lab-role: gpu
      containers:
        - name: inventory
          image: registry.redhat.io/rhaii/vllm-cuda-rhel9@sha256:ad06abf3bb5235ebb5b2df84cd1b9fd09e823f0ff2eebfc82bb4590275ccfe0b
          command: [bash, -lc]
          args:
            - nvidia-smi -L; echo; nvidia-smi topo -m
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
              nvidia.com/gpu: "2"
            limits:
              cpu: "1"
              memory: 1Gi
              nvidia.com/gpu: "2"
EOF

oc wait --for=condition=Complete job/week6-gpu-inventory \
  -n rhoai-tp-lab --timeout=300s
oc logs job/week6-gpu-inventory -n rhoai-tp-lab
oc delete job week6-gpu-inventory -n rhoai-tp-lab
```

`GPU 0`, `GPU 1` 두 행과 topology 표가 출력돼야 한다. `NV#` 연결이 없고 `PHB`, `PXB` 또는 `SYS`로 보이는 것은 이 PCIe passthrough 구성에서 예상되는 결과다.

### 공식 문서

- [RHOAI 3.4 - Customizing the vLLM model-serving runtime](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/configuring_your_model-serving_platform/customizing_model_deployments)
- [RHOAI 3.4 - Deploying a model stored in an OCI image by using the CLI](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/pdf/deploying_models/Red_Hat_OpenShift_AI_Self-Managed-3.4-Deploying_models-en-US.pdf)
- [vLLM - Parallelism and Scaling](https://docs.vllm.ai/en/stable/serving/parallelism_scaling/)
- [NVIDIA GPU Operator - Time-Slicing GPUs in Kubernetes](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
- [Qwen2.5 0.5B Instruct commit 7ae5576 - config.json](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/blob/7ae557604adf67be50417f59c2c2f167def9a775/config.json)
