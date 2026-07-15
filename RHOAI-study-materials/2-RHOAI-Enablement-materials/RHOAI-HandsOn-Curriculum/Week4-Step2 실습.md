# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 4 - Step 2 Kueue Cohort와 팀별 Queue 구성

> 사전 활성화: [Week3 Day12](Week3-Day12%20실습.md)의 Kueue 컨트롤러와 [Week4 Step 1](Week4-Step1%20실습.md)의 Time-Slicing 슬롯 4개가 필요하다.

Team A와 Team B에 nominal GPU quota 2개씩을 주고, 같은 Cohort에서 사용하지 않는 quota를 빌릴 수 있게 구성한다.

### Queue 리소스 적용
```bash
oc apply -f /tmp/python3/manifests/week4-kueue-cohort.yaml
```

생성되는 주요 리소스는 다음과 같다.

| 리소스 | 역할 |
|---|---|
| `week4-shared-gpu` ResourceFlavor | `lab-role=gpu` 노드의 공유 GPU를 선택 |
| `week4-gpu-cohort` Cohort | 두 ClusterQueue가 미사용 quota를 공유하는 범위 |
| `gpu-team-a-cq`, `gpu-team-b-cq` | 각 팀의 nominal GPU quota 2개와 회수 정책 |
| 각 Namespace의 `team-lq` | 사용자가 Job에서 지정하는 namespace-scoped queue |
| `week4-borrower`, `week4-owner` | 빌리는 workload와 quota 소유 workload를 구분하는 우선순위 |

### GPU 부하 스크립트 ConfigMap 생성
두 Namespace의 Job이 같은 스크립트를 mount하도록 ConfigMap을 만든다.

```bash
for NS in gpu-team-a gpu-team-b; do
  oc create configmap week4-gpu-load -n "$NS" \
    --from-file=gpu_share_load.py=/tmp/python3/models/gpu_share_load.py \
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

두 ClusterQueue가 `Active=True`이고 각각 `nvidia.com/gpu` nominal quota 2를 표시해야 한다. `cohortName`은 두 Queue 모두 `week4-gpu-cohort`다.

### Namespace 관리 범위 확인
```bash
oc get namespace gpu-team-a gpu-team-b \
  --show-labels | grep kueue.openshift.io/managed
```

이 Namespace에서는 `team-lq`를 지정한 Job을 사용한다. 다음 단계의 Job은 처음에 `suspend: true`로 생성되고 Kueue가 admission한 뒤 `false`로 변경한다.
