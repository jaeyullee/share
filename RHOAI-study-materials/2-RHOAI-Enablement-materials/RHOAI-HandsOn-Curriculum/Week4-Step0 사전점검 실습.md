# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 4 - GPU 공유 사전점검

> 사전 활성화: [Week3 Day11](Week3-Day11%20실습.md)의 NFD/KMM/NVIDIA GPU Operator와 [Week3 Day12](Week3-Day12%20실습.md)의 Red Hat build of Kueue를 먼저 구성한다.

GPU 공유와 Kueue cohort 실습 전에 물리 GPU, NVIDIA Device Plugin, Kueue API 버전을 확인하고 기존 설정을 백업한다.

### 커리큘럼 보정 사항
현재 랩의 `ocp-w01-gpu`에는 passthrough된 RTX 5060 Ti가 **1개** 있다. 이 노드에서는 다음과 같이 실습한다.

| 원본 구상 | 검증 결과와 실습 방식 |
|---|---|
| GPU 0은 Time-Slicing, GPU 1은 MPS | 현재 물리 GPU가 1개이며, NVIDIA Device Plugin은 한 노드의 모든 GPU에 같은 공유 방식을 적용한다. 혼합할 수 없다. |
| Time-Slicing 2개 + MPS 2개 | 기본 실습은 Time-Slicing replica 4개다. MPS는 노드 전체를 전환하는 선택 비교 실습으로만 수행한다. |
| 한 Job이 GPU 4개 요청 | 공유 GPU 요청 1은 접근 슬롯 1개다. 독립 Job 4개가 각각 1개를 요청하도록 구성한다. |
| 임의의 GPU 리소스명으로 방식 분리 | `renameByDefault`는 `nvidia.com/gpu.shared`로만 바꾼다. 한 노드에서 `gpu.shared-ts`와 `gpu.mps` 같은 임의 분리는 할 수 없다. |

Time-Slicing replica는 물리 GPU나 고정된 연산 지분이 아니다. 메모리와 장애 영역도 격리하지 않는다. 이 실습의 `nvidia.com/gpu: 4`는 동시에 admission할 수 있는 공유 접근 슬롯 4개라는 뜻이다.

### Operator와 API 확인
```bash
oc get csv -A | grep -Ei 'nfd|kernel-module|gpu-operator|kueue'
oc get clusterpolicy gpu-cluster-policy
oc get kueues.kueue.openshift.io cluster

oc api-resources --api-group=kueue.x-k8s.io
oc explain clusterqueue.spec.cohortName
oc explain clusterqueue.spec.resourceGroups.flavors.resources.lendingLimit
```

이 자료는 Red Hat build of Kueue 1.3.1의 `kueue.x-k8s.io/v1beta2`를 기준으로 한다. `cohortName` 또는 `lendingLimit`가 없으면 설치된 Kueue 버전이 다르므로 매니페스트를 바로 적용하지 않는다.

### 물리 GPU와 공유 상태 확인
```bash
oc debug node/ocp-w01-gpu -- chroot /host \
  lspci -nn | grep -i nvidia

oc get node ocp-w01-gpu \
  -o jsonpath='{.status.capacity.nvidia\.com/gpu}{"/"}{.status.allocatable.nvidia\.com/gpu}{"\n"}'

oc get node ocp-w01-gpu \
  -o jsonpath='{.metadata.labels.nvidia\.com/mig\.capable}{"\n"}'
```

`lspci`에는 NVIDIA display 장치 1개와 같은 카드의 audio function이 보인다. audio function을 두 번째 GPU로 세지 않는다. GPU Operator 구성이 끝난 직후 공유 설정 전 capacity/allocatable은 `1/1`, MIG 가능 여부는 이 RTX 5060 Ti에서 `false`가 정상이다.

### 기존 Device Plugin 설정 백업
```bash
oc get clusterpolicy gpu-cluster-policy -o json | \
  jq -c '.spec.devicePlugin.config // null' \
  > /tmp/week4-device-plugin-config-before.json

oc get node ocp-w01-gpu -o json | \
  jq -r '.metadata.labels["nvidia.com/device-plugin.config"] // "__ABSENT__"' \
  > /tmp/week4-node-config-label-before

cat /tmp/week4-device-plugin-config-before.json
cat /tmp/week4-node-config-label-before
```

두 파일은 Step 6의 원복에 사용하므로 실습이 끝날 때까지 삭제하지 않는다.

### 실습 파일 확인
```bash
ls /tmp/python3/manifests/week4-*.yaml
ls /tmp/python3/models/gpu_share_load.py
```

추가 dataset과 학습 모델은 필요하지 않다. `gpu_share_load.py`가 PyTorch 행렬 연산으로 일정한 CUDA 부하를 만든다.

### 공식 문서
- [Red Hat OpenShift AI 3.4 - Working with accelerators](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/pdf/working_with_accelerators/Red_Hat_OpenShift_AI_Self-Managed-3.4-Working_with_accelerators-en-US.pdf)
- [NVIDIA GPU Operator - Time-Slicing GPUs in Kubernetes](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
- [NVIDIA Kubernetes Device Plugin - Shared access to GPUs](https://github.com/NVIDIA/k8s-device-plugin#shared-access-to-gpus)
- [Kueue - Cohort](https://kueue.sigs.k8s.io/docs/concepts/cohort/)
- [Kueue - ClusterQueue](https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/)

> Cohort는 Kueue의 quota 공유 기능을 확인하는 추가 스터디다. 고객사 적용 전에는 사용 중인 RHOAI/RHBOK 조합의 Red Hat 지원 범위를 별도로 확인한다.
