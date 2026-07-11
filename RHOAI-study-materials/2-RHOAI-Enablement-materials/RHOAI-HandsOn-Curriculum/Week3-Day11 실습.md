# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 3 - Day11

NFD, KMM, NVIDIA GPU Operator를 설치해서 GPU worker의 GPU를 OpenShift 리소스로 노출하고 RHOAI HardwareProfile을 만든다.

### GPU worker 사전 확인
```bash
oc get node -l node-role.kubernetes.io/gpu -o wide
oc get node ocp-w01-gpu \
  -o jsonpath='{.status.allocatable.nvidia\.com/gpu}{"\n"}'
```

GPU Operator 설치 전에는 두 번째 명령이 빈 값을 반환할 수 있다.

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

CSV가 `Succeeded`가 된 뒤 `NodeFeatureDiscovery`를 생성한다. OCP 4.22에서는 `spec.operand.image`를 명시한다.

```bash
oc apply -f - <<'EOF'
apiVersion: nfd.openshift.io/v1
kind: NodeFeatureDiscovery
metadata:
  name: nfd-instance
  namespace: openshift-nfd
spec:
  operand:
    image: registry.redhat.io/openshift4/ose-node-feature-discovery-rhel9:v4.22
    imagePullPolicy: IfNotPresent
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
spec:
  targetNamespaces:
    - openshift-kmm
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

### NVIDIA GPU Operator 설치
현재 미러 CatalogSource의 기본 채널은 `v26.3`이다. `stable` 채널로 추측해서 설치하지 않는다.

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

기본 `ClusterPolicy`가 없을 때만 다음 최소 설정을 적용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: nvidia.com/v1
kind: ClusterPolicy
metadata:
  name: gpu-cluster-policy
spec:
  driver:
    enabled: true
  toolkit:
    enabled: true
  devicePlugin:
    enabled: true
  dcgmExporter:
    enabled: true
  nodeStatusExporter:
    enabled: true
  migManager:
    enabled: false
EOF

oc get clusterpolicy gpu-cluster-policy
oc get pods -n nvidia-gpu-operator -o wide
```

드라이버 빌드와 validator가 완료될 때까지 시간이 걸릴 수 있다.

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
  docker://192.168.10.50:5000/ocp-mirror/rhaii/vllm-cuda-rhel9:<MIRRORED_TAG_OR_DIGEST> \
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

