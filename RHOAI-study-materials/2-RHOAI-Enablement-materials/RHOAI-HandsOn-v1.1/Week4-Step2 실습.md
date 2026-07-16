# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 4 - Step 2 Kueue Cohort와 팀별 Queue 구성

> 사전 활성화: [Week3 Day12](<Week3-Day12 실습.md>)의 Kueue 컨트롤러와 [Week4 Step 1](<Week4-Step1 실습.md>)의 Time-Slicing 슬롯 4개가 필요하다.

Team A와 Team B에 nominal GPU quota 2개씩을 주고, 같은 Cohort에서 사용하지 않는 quota를 빌릴 수 있게 구성한다.

### Queue 리소스 적용
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: gpu-team-a
  labels:
    kueue.openshift.io/managed: "true"
---
apiVersion: v1
kind: Namespace
metadata:
  name: gpu-team-b
  labels:
    kueue.openshift.io/managed: "true"
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata:
  name: week4-shared-gpu
spec:
  nodeLabels:
    lab-role: gpu
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: Cohort
metadata:
  name: week4-gpu-cohort
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: gpu-team-a-cq
spec:
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: gpu-team-a
  cohortName: week4-gpu-cohort
  queueingStrategy: BestEffortFIFO
  preemption:
    reclaimWithinCohort: Any
    withinClusterQueue: LowerPriority
  resourceGroups:
    - coveredResources: [nvidia.com/gpu, cpu, memory]
      flavors:
        - name: week4-shared-gpu
          resources:
            - name: nvidia.com/gpu
              nominalQuota: 2
            - name: cpu
              nominalQuota: 4
            - name: memory
              nominalQuota: 8Gi
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: gpu-team-b-cq
spec:
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: gpu-team-b
  cohortName: week4-gpu-cohort
  queueingStrategy: BestEffortFIFO
  preemption:
    reclaimWithinCohort: Any
    withinClusterQueue: LowerPriority
  resourceGroups:
    - coveredResources: [nvidia.com/gpu, cpu, memory]
      flavors:
        - name: week4-shared-gpu
          resources:
            - name: nvidia.com/gpu
              nominalQuota: 2
            - name: cpu
              nominalQuota: 4
            - name: memory
              nominalQuota: 8Gi
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: team-lq
  namespace: gpu-team-a
spec:
  clusterQueue: gpu-team-a-cq
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: team-lq
  namespace: gpu-team-b
spec:
  clusterQueue: gpu-team-b-cq
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: WorkloadPriorityClass
metadata:
  name: week4-borrower
value: 100
description: Week 4 workload that can use borrowed cohort quota
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: WorkloadPriorityClass
metadata:
  name: week4-owner
value: 1000
description: Week 4 workload reclaiming its queue's nominal quota
EOF
```

생성되는 주요 리소스는 다음과 같다.

| 리소스 | 역할 |
|---|---|
| `week4-shared-gpu` ResourceFlavor | `lab-role=gpu` 노드의 공유 GPU를 선택 |
| `week4-gpu-cohort` Cohort | 두 ClusterQueue가 미사용 quota를 공유하는 범위 |
| `gpu-team-a-cq`, `gpu-team-b-cq` | 각 팀의 nominal GPU 2개, CPU 4, 메모리 8Gi quota와 회수 정책 |
| 각 Namespace의 `team-lq` | 사용자가 Job에서 지정하는 namespace-scoped queue |
| `week4-borrower`, `week4-owner` | 빌리는 workload와 quota 소유 workload를 구분하는 우선순위 |

### GPU 부하 스크립트 ConfigMap 생성
두 Namespace의 Job이 같은 스크립트를 mount하도록 ConfigMap을 만든다.

```bash
cd /tmp/python3
RHOAI_HANDSON_DIR="${RHOAI_HANDSON_DIR:-$PWD}"
test -f "$RHOAI_HANDSON_DIR/models/gpu_share_load.py"

for NS in gpu-team-a gpu-team-b; do
  oc create configmap week4-gpu-load -n "$NS" \
    --from-file=gpu_share_load.py="$RHOAI_HANDSON_DIR/models/gpu_share_load.py" \
    --dry-run=client -o yaml | oc apply -f -
done
```

### 구성 확인
```bash
oc get cohort week4-gpu-cohort
oc get resourceflavor week4-shared-gpu
oc get clusterqueue gpu-team-a-cq gpu-team-b-cq
oc get localqueue -n gpu-team-a
oc get localqueue -n gpu-team-b

oc describe clusterqueue gpu-team-a-cq
oc describe clusterqueue gpu-team-b-cq
```

두 ClusterQueue가 `Active=True`이고 각각 `nvidia.com/gpu=2`, `cpu=4`, `memory=8Gi` nominal quota를 표시해야 한다. `cohortName`은 두 Queue 모두 `week4-gpu-cohort`다.

Kueue는 Job이 요청하는 모든 자원을 ClusterQueue에서 flavor에 할당할 수 있어야 admission한다. 따라서 GPU만 비교하는 실습이어도 Job의 `cpu`와 `memory` 요청을 `coveredResources`와 quota에 포함한다. CPU와 메모리 quota는 네 GPU Job의 총 요청보다 넉넉하게 설정해 이후 단계의 admission 수가 GPU quota에 의해 결정되게 한다.

### Namespace 관리 범위 확인
```bash
oc get namespace gpu-team-a gpu-team-b \
  --show-labels | grep kueue.openshift.io/managed
```

이 Namespace에서는 `team-lq`를 지정한 Job을 사용한다. 다음 단계의 Job은 처음에 `suspend: true`로 생성되고 Kueue가 admission한 뒤 `false`로 변경한다.
