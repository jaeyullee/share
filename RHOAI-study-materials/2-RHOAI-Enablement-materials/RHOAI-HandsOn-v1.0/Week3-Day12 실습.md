# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 실습
## week 3 - Day12

> 사전 활성화: [Week1 Day1&2 - Queue 기반 Workbench 구성](<Week1-Day1&2-환경구성.md#queue-기반-workbench-구성>)을 먼저 확인한다. GPU Time-Slicing까지 수행하면 [GPU Workbench·서빙·학습 구성](<Week1-Day1&2-환경구성.md#gpu-workbench서빙학습-구성>)도 필요하다.

> Red Hat build of Kueue로 CPU/GPU 워크로드의 quota, admission, priority를 관리하고 NVIDIA Time-Slicing을 확인한다.
> RHOAI 3.4에서는 embedded Kueue 대신 Red Hat build of Kueue Operator를 사용한다. shared cohort는 RHOAI 3.4 지원 범위에서 제외하므로 이 실습에서도 사용하지 않는다.

Kueue Cohort는 여러 `ClusterQueue`를 같은 quota 공유 그룹으로 묶는 기능이다. 예를 들어 Team A와 Team B에 GPU nominal quota를 각각 2개씩 배정했을 때, Team B가 사용하지 않는 quota를 Team A가 같은 cohort 안에서 빌려 최대 4개까지 admission 받을 수 있다. Team B가 다시 quota를 요구하면 reclaim/preemption 정책에 따라 빌려준 quota를 회수할 수 있다.

이 기능은 NVIDIA Time-Slicing과 다르다. Cohort는 **어떤 workload를 실행시킬지 결정하는 Kueue quota**를 공유하고, Time-Slicing은 admission된 여러 workload가 **하나의 물리 GPU 실행시간**을 나눠 사용하게 한다. Day12 기본 실습은 지원 범위에 맞춰 각 ClusterQueue를 독립적으로 운영하고, cohort 차용·회수 동작은 지원 범위를 별도 확인하는 Week4 추가 스터디에서 다룬다.

### Kueue Operator 설치
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-kueue-operator
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: openshift-kueue-operator
  namespace: openshift-kueue-operator
spec: {} # Red Hat build of Kueue 1.3은 AllNamespaces 설치 모드다.
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: kueue-operator
  namespace: openshift-kueue-operator
spec:
  channel: stable-v1.3
  installPlanApproval: Automatic
  name: kueue-operator
  source: cs-redhat-operator-index-v4-22
  sourceNamespace: openshift-marketplace
EOF

oc get csv,subscription,pods -n openshift-kueue-operator
```

### Kueue 컨트롤러와 RHOAI 연동 활성화
Operator 설치 후 현재 CSV의 예제대로 Kueue 컨트롤러 인스턴스를 먼저 생성한다.

```bash
oc apply -f - <<'EOF'
apiVersion: kueue.openshift.io/v1
kind: Kueue
metadata:
  name: cluster
spec:
  managementState: Managed
  config:
    integrations:
      frameworks:
        - BatchJob
        - RayJob
        - RayCluster
        - JobSet
        - PyTorchJob
        - TrainJob
        - Pod
        - Deployment
        - StatefulSet
EOF

oc get kueues.kueue.openshift.io cluster
```

`BatchJob`만 등록하면 일반 Job은 처리할 수 있지만, 대시보드 Workbench가 만드는 StatefulSet과 Trainer/Ray workload는 admission되지 않는다. 위 목록은 Day12 Workbench, Trainer, Ray 검증에 사용한 RHBOK 1.3.1 구성이다.

RHOAI가 별도 설치된 Kueue를 사용하도록 `Unmanaged`로 설정한다.

```bash
oc patch dsc default-dsc --type=merge \
  -p '{"spec":{"components":{"kueue":{"managementState":"Unmanaged","defaultClusterQueueName":"team-cq","defaultLocalQueueName":"team-lq"}}}}'

oc get dsc default-dsc \
  -o jsonpath='{.spec.components.kueue}{"\n"}'
oc get kueue -A
oc get pods -A | grep -i kueue
```

### Kueue 관리 Namespace 지정
```bash
oc label namespace jukebox kueue.openshift.io/managed=true --overwrite
```

이 label이 있는 프로젝트에서는 queue를 지정하지 않은 대상 워크로드를 validating webhook이 차단할 수 있다.

### CPU ResourceFlavor와 Queue 생성
```bash
oc apply -f - <<'EOF'
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata:
  name: cpu-flavor
spec:
  nodeLabels:
    lab-role: cpu
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: team-cq
spec:
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: jukebox
  queueingStrategy: BestEffortFIFO
  preemption:
    withinClusterQueue: LowerPriority
  resourceGroups:
    - coveredResources:
        - cpu
        - memory
      flavors:
        - name: cpu-flavor
          resources:
            - name: cpu
              nominalQuota: "4"
            - name: memory
              nominalQuota: 8Gi
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: team-lq
  namespace: jukebox
spec:
  clusterQueue: team-cq
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: WorkloadPriorityClass
metadata:
  name: day12-low
value: 100
description: "Day12 low priority workload"
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: WorkloadPriorityClass
metadata:
  name: day12-high
value: 1000
description: "Day12 high priority workload"
EOF

oc get resourceflavor cpu-flavor
oc get clusterqueue team-cq
oc get localqueue team-lq -n jukebox
```

Red Hat build of Kueue 1.3.1은 이 클러스터에서 `v1beta2`를 제공한다. 다른 버전에서는 `oc api-resources --api-group=kueue.x-k8s.io`로 제공 버전을 먼저 확인한다.

`ClusterQueue/team-cq`가 CPU 4개와 memory 8Gi quota를 실제로 보유하고 admission을 결정한다. `LocalQueue/jukebox/team-lq`는 이 ClusterQueue를 가리키는 namespace-scoped 입구이며 자체 quota를 나눠 갖지 않는다.

여러 Namespace의 LocalQueue가 같은 ClusterQueue를 가리키면 모두 같은 quota pool에서 경쟁한다. 팀별로 고정 quota를 분리하려면 팀마다 별도 ClusterQueue를 만들고 각 LocalQueue를 해당 ClusterQueue에 연결해야 한다. 별도 ClusterQueue 사이의 유휴 quota까지 빌려 쓰게 하려는 기능이 앞에서 설명한 Cohort다.

### 기본 Queue admission 확인
```bash
oc apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: day12-normal
  namespace: jukebox
  labels:
    kueue.x-k8s.io/queue-name: team-lq
    kueue.x-k8s.io/priority-class: day12-low
spec:
  suspend: true
  template:
    spec:
      restartPolicy: Never
      nodeSelector:
        lab-role: cpu
      containers:
        - name: workload
          image: registry.redhat.io/rhoai/odh-pipeline-runtime-datascience-cpu-py312-rhel9@sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661
          command: ["sh", "-c", "echo admitted; sleep 60"]
          resources:
            requests:
              cpu: "1"
              memory: 1Gi
EOF

oc get job day12-normal -n jukebox -w
```

Kueue가 admission하면 Job의 `spec.suspend`가 `false`로 바뀌고 Pod가 실행된다.

```bash
oc get workload -n jukebox
oc describe workload -n jukebox
oc logs job/day12-normal -n jukebox
```

### 우선순위와 선점 검증
낮은 우선순위 Job이 quota를 사용 중일 때 높은 우선순위 Job을 제출한다.

```bash
oc apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: day12-low
  namespace: jukebox
  labels:
    kueue.x-k8s.io/queue-name: team-lq
    kueue.x-k8s.io/priority-class: day12-low
spec:
  suspend: true
  template:
    spec:
      restartPolicy: Never
      nodeSelector:
        lab-role: cpu
      containers:
        - name: workload
          image: registry.redhat.io/rhoai/odh-pipeline-runtime-datascience-cpu-py312-rhel9@sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661
          command: ["sh", "-c", "echo low-started; sleep 600"]
          resources:
            requests:
              cpu: "4"
              memory: 4Gi
EOF

oc wait --for=jsonpath='{.spec.suspend}'=false \
  job/day12-low -n jukebox --timeout=120s

oc apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: day12-high
  namespace: jukebox
  labels:
    kueue.x-k8s.io/queue-name: team-lq
    kueue.x-k8s.io/priority-class: day12-high
spec:
  suspend: true
  template:
    spec:
      restartPolicy: Never
      nodeSelector:
        lab-role: cpu
      containers:
        - name: workload
          image: registry.redhat.io/rhoai/odh-pipeline-runtime-datascience-cpu-py312-rhel9@sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661
          command: ["sh", "-c", "echo high-started; sleep 60"]
          resources:
            requests:
              cpu: "4"
              memory: 4Gi
EOF

oc get workload -n jukebox -w
```

`oc describe workload`의 admission, eviction, preemption 이벤트에서 높은 우선순위 workload가 먼저 실행되는지 확인한다.

### NVIDIA Time-Slicing 설정
GPU Operator와 Day11의 GPU가 정상인 경우에만 진행한다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: day12-time-slicing
  namespace: nvidia-gpu-operator
data:
  any: |-
    version: v1
    flags:
      migStrategy: none
    sharing:
      timeSlicing:
        renameByDefault: false
        failRequestsGreaterThanOne: true
        resources:
          - name: nvidia.com/gpu
            replicas: 4
EOF

oc patch clusterpolicy gpu-cluster-policy --type=merge \
  -p '{"spec":{"devicePlugin":{"config":{"name":"day12-time-slicing","default":"any"}}}}'

oc label node ocp-w01-gpu \
  nvidia.com/device-plugin.config=any --overwrite
```

device plugin이 다시 기동된 뒤 allocatable이 4로 증가하는지 확인한다.

```bash
oc get pods -n nvidia-gpu-operator -w
oc get node ocp-w01-gpu \
  -o jsonpath='{.status.allocatable.nvidia\.com/gpu}{"\n"}'
```

> Time-Slicing의 `nvidia.com/gpu: 4`는 물리 GPU가 4개라는 의미가 아니다. 네 workload가 하나의 GPU 실행시간과 메모리를 공유할 수 있다는 뜻이며 메모리 격리는 제공하지 않는다.

### GPU ResourceFlavor 추가
```bash
oc apply -f - <<'EOF'
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata:
  name: gpu-shared-flavor
spec:
  nodeLabels:
    lab-role: gpu
EOF
```

GPU queue를 만들 때 `coveredResources: [nvidia.com/gpu]`와 `nominalQuota: 4`를 사용한다. CPU queue와 분리하면 CPU 실습에 영향을 주지 않고 GPU quota를 조정할 수 있다.
