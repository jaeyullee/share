# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 3 - Day11

> **환경별 재확인**: GPU 모델, PCI 주소, VMID, IOMMU/VFIO, GPU Operator channel과 CatalogSource는 검증 환경 값이다. 설치 전에 대상 노드의 실제 장치와 지원 조합을 확인한다. 공통 경계 조건은 [실습자료 검토 항목](<00-실습자료-검토항목.md#환경별-재확인>)을 참고한다.

> 배경 참고 및 전제 확인: [Week1 Day1&2 - GPU Workbench·서빙·학습 구성](<Week1-Day1&2-환경구성.md#gpu-workbench서빙학습-구성>)은 목적과 전체 순서를 요약한 인덱스다. NFD, KMM, NVIDIA GPU Operator와 HardwareProfile의 실제 설치는 이 Day11에서 모두 수행하므로 미리 중복 설치하지 않는다. 단, GPU PCI passthrough와 `cs-redhat-gpu-localstorage-v4-22`, `cs-certified-operator-index-v4-22` CatalogSource 및 관련 mirror는 준비되어 있어야 한다.

NFD, KMM, NVIDIA GPU Operator를 설치해서 GPU worker의 GPU를 OpenShift 리소스로 노출하고 RHOAI HardwareProfile을 만든다.

### GPU worker 사전 확인
```bash
oc get node -l lab-role=gpu -o wide
oc debug node/ocp-w01-gpu -- chroot /host lspci -nn | grep -i nvidia
oc get node ocp-w01-gpu \
  -o jsonpath='{.status.allocatable.nvidia\.com/gpu}{"\n"}'
```

`lspci`에서 NVIDIA 장치가 보여야 설치를 계속할 수 있다. 출력이 없으면 VM/물리 노드에 GPU PCI 장치가 연결되지 않은 상태이므로 GPU Operator로 해결할 수 없다. GPU Operator 설치 전에는 allocatable 값이 빈 값 또는 `0`을 반환할 수 있다. ClusterPolicy와 device plugin이 정상화된 뒤에는 검증 환경 기준 `1`이어야 한다.

Proxmox VM에서 장치가 보이지 않으면 host의 VFIO 바인딩과 VM의 `hostpci`를 각각 확인한다. 검증 환경의 GPU worker는 VMID `102`, 첫 번째 GPU는 `01:00`이다.

```bash
# Proxmox host
lspci -nnk -s 01:00.0
qm config 102 | grep '^hostpci'

# hostpci가 없을 때: 먼저 OpenShift에서 노드를 drain한 뒤 VM을 종료한다.
qm set 102 --hostpci0 01:00,pcie=1,x-vga=1
qm start 102
```

`01:00.0`과 `01:00.1`은 같은 IOMMU group에 있어야 하고 host에서는 `vfio-pci`, 재기동한 RHCOS에서는 `NVIDIA GB206 [GeForce RTX 5060 Ti]`로 보여야 한다. VM 설정 변경 전에는 `oc adm cordon`과 `oc adm drain --ignore-daemonsets --delete-emptydir-data`로 일반 workload를 비운다.

### Node Feature Discovery Operator 설치
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-nfd
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: openshift-nfd
  namespace: openshift-nfd
spec:
  targetNamespaces:
    - openshift-nfd
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: nfd
  namespace: openshift-nfd
spec:
  channel: stable
  installPlanApproval: Automatic
  name: nfd
  source: cs-redhat-gpu-localstorage-v4-22
  sourceNamespace: openshift-marketplace
EOF

oc get csv,subscription,pods -n openshift-nfd
```

CSV가 `Succeeded`가 된 뒤 `NodeFeatureDiscovery`를 생성한다. 설치된 CSV의 `alm-examples`와 같이 operand 이미지는 Operator의 관련 이미지 환경변수에 맡기고 고정하지 않는다.

웹 콘솔에서 **NodeFeatureDiscovery 생성**을 눌렀을 때 표시되는 기본 YAML은 설치된 NFD Operator CSV의 `alm-examples`이므로 그대로 생성해도 된다. 다음 항목만 확인한다.

- `metadata.name: nfd-instance`
- `metadata.namespace: openshift-nfd`
- `workerConfig.configData`의 PCI `deviceClassWhitelist`에 GPU class인 `"03"` 포함
- `deviceLabelFields`에 `vendor` 포함

현재 NFD 4.22 기본 예제에는 `"0200"`, `"03"`, `"12"`가 들어 있다. 아래 CLI 예제는 랩에 필요한 네트워크 class `0200`과 GPU class `03`만 남긴 축약본이며, 웹 콘솔 기본값의 `12`를 유지해도 문제없다. 같은 클러스터에 `nfd-instance`를 중복 생성하지 않고 GUI 또는 CLI 중 한 가지 방법만 사용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: nfd.openshift.io/v1
kind: NodeFeatureDiscovery
metadata:
  name: nfd-instance
  namespace: openshift-nfd
spec:
  operand:
    imagePullPolicy: IfNotPresent
    servicePort: 12000
  workerConfig:
    configData: |
      core:
        sleepInterval: 60s
      sources:
        pci:
          deviceClassWhitelist:
            - "0200"
            - "03"
          deviceLabelFields:
            - vendor
EOF

oc get pods -n openshift-nfd
oc get node ocp-w01-gpu --show-labels | grep -o 'feature.node.kubernetes.io/pci-10de[^,]*'
```

`pci-10de` label의 `10de`는 NVIDIA PCI vendor ID다.

### Kernel Module Management Operator 설치
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-kmm
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: openshift-kmm
  namespace: openshift-kmm
spec: {} # KMM 2.6은 AllNamespaces 설치 모드만 지원한다.
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: kernel-module-management
  namespace: openshift-kmm
spec:
  channel: stable
  installPlanApproval: Automatic
  name: kernel-module-management
  source: cs-redhat-gpu-localstorage-v4-22
  sourceNamespace: openshift-marketplace
EOF

oc get csv,subscription,pods -n openshift-kmm
```

KMM OperatorGroup에 `targetNamespaces`를 지정하면 `UnsupportedOperatorGroup`으로 실패한다.

### NVIDIA GPU Operator 설치
현재 미러 CatalogSource의 기본 채널은 `v26.3`이다. `stable` 채널로 추측해서 설치하지 않는다.

GPU Operator 26.3의 operand는 digest가 포함된 `nvcr.io/nvidia/...` 이미지를 사용한다. `ImageTagMirrorSet`만 있으면 태그 pull은 미러링되지만 digest pull은 외부 `nvcr.io`로 나가므로, 각 operand repository에 대한 `ImageDigestMirrorSet`도 있어야 한다. 다음 명령에서 `k8s-driver-manager` 항목이 `pull-from-mirror = "digest-only"`로 보여야 한다.

```bash
oc debug node/ocp-w01-gpu -- chroot /host \
  grep -A6 'nvcr.io/nvidia/cloud-native/k8s-driver-manager' \
  /etc/containers/registries.conf
```

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: nvidia-gpu-operator
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: nvidia-gpu-operator
  namespace: nvidia-gpu-operator
spec:
  targetNamespaces:
    - nvidia-gpu-operator
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: gpu-operator-certified
  namespace: nvidia-gpu-operator
spec:
  channel: v26.3
  installPlanApproval: Automatic
  name: gpu-operator-certified
  source: cs-certified-operator-index-v4-22
  sourceNamespace: openshift-marketplace
EOF

oc get csv,subscription,pods -n nvidia-gpu-operator
```

### ClusterPolicy 생성
Operator가 제공하는 `alm-examples`를 확인하고 현재 CSV의 기본 예제로 생성한다.

```bash
GPU_CSV=$(oc get csv -n nvidia-gpu-operator \
  -o jsonpath='{.items[?(@.spec.displayName=="NVIDIA GPU Operator")].metadata.name}')

oc get csv "$GPU_CSV" -n nvidia-gpu-operator \
  -o jsonpath='{.metadata.annotations.alm-examples}' | jq .
```

기본 `ClusterPolicy`가 없을 때만 CSV의 현재 예제를 사용한다. RTX 5060 Ti 실습에 필요하지 않은 MIG, vGPU, sandbox 계열 기능은 비활성화한다.

```bash
oc get csv "$GPU_CSV" -n nvidia-gpu-operator \
  -o jsonpath='{.metadata.annotations.alm-examples}' | \
  jq '.[0]
      | .spec.migManager.enabled=false
      | .spec.vgpuDeviceManager.enabled=false
      | .spec.sandboxDevicePlugin.enabled=false
      | .spec.kataSandboxDevicePlugin.enabled=false
      | .spec.vfioManager.enabled=false
      | .spec.ccManager.enabled=false' | \
  oc apply -f -

oc get clusterpolicy gpu-cluster-policy
oc get pods -n nvidia-gpu-operator -o wide
```

드라이버 빌드와 validator가 완료될 때까지 시간이 걸릴 수 있다. 테스트 환경 기준 7분 이상 소요.

```bash
oc get clusterpolicy gpu-cluster-policy -o yaml
oc get events -n nvidia-gpu-operator --sort-by=.lastTimestamp | tail -30
```

### GPU 리소스 확인
```bash
oc get node ocp-w01-gpu \
  -o jsonpath='{.status.capacity.nvidia\.com/gpu}{"/"}{.status.allocatable.nvidia\.com/gpu}{"\n"}'

oc get pods -n nvidia-gpu-operator -o wide
```

### GPU 할당 Pod 실행
GPU test image는 모델 이미지 레지스트리 `5010`에 미리 반입한다.

```bash
skopeo copy --src-tls-verify=false --dest-tls-verify=false \
  --src-creds '<MIRROR_REGISTRY_ID>:<MIRROR_REGISTRY_PW>' \
  --dest-creds '<MODEL_REGISTRY_ID>:<MODEL_REGISTRY_PW>' \
  docker://192.168.10.50:5000/ocp-mirror/rhaii/vllm-cuda-rhel9@sha256:ad06abf3bb5235ebb5b2df84cd1b9fd09e823f0ff2eebfc82bb4590275ccfe0b \
  docker://192.168.10.50:5010/rhaii/vllm-cuda-rhel9:rhoai-3.4
```

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: day11-nvidia-smi
  namespace: jukebox
spec:
  restartPolicy: Never
  nodeSelector:
    lab-role: gpu
  containers:
    - name: nvidia-smi
      image: 192.168.10.50:5010/rhaii/vllm-cuda-rhel9:rhoai-3.4
      command: ["bash", "-c", "nvidia-smi; sleep 10"]
      resources:
        limits:
          nvidia.com/gpu: "1"
EOF

oc wait --for=jsonpath='{.status.phase}'=Succeeded \
  pod/day11-nvidia-smi -n jukebox --timeout=300s
oc logs pod/day11-nvidia-smi -n jukebox
```

로그에서 GPU 모델, 드라이버, CUDA 버전이 출력되면 GPU 할당까지 정상이다.

### HardwareProfile 생성
RHOAI 3.4의 `HardwareProfile` v1에서는 표시 이름과 활성화 여부를 annotation으로 설정한다.

```bash
oc apply -f - <<'EOF'
apiVersion: infrastructure.opendatahub.io/v1
kind: HardwareProfile
metadata:
  name: gpu-small
  namespace: redhat-ods-applications
  labels:
    app.kubernetes.io/part-of: hardwareprofile
    app.opendatahub.io/hardwareprofile: "true"
  annotations:
    opendatahub.io/display-name: "GPU Small - 1 GPU"
    opendatahub.io/description: "1 NVIDIA GPU, 2 CPU, 4 GiB memory"
    opendatahub.io/disabled: "false"
spec:
  identifiers:
    - displayName: CPU
      identifier: cpu
      minCount: 1
      defaultCount: 2
      maxCount: 4
      resourceType: CPU
    - displayName: Memory
      identifier: memory
      minCount: 2Gi
      defaultCount: 4Gi
      maxCount: 16Gi
      resourceType: Memory
    - displayName: GPU
      identifier: nvidia.com/gpu
      minCount: 1
      defaultCount: 1
      maxCount: 1
      resourceType: Accelerator
  scheduling:
    type: Node
    node:
      nodeSelector:
        lab-role: gpu
EOF

oc get hardwareprofile gpu-small -n redhat-ods-applications -o yaml
```

RHOAI 대시보드에서 Workbench 또는 Model deployment 생성 시 `GPU Small - 1 GPU` 프로필이 표시되는지 확인한다.

> RTX 5060 Ti는 MIG 실습 대상이 아니다. GPU 공유는 Day12에서 Time-Slicing으로 진행한다.
