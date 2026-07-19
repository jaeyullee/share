# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 4 - Step 6 Cohort 제거와 완전 격리

> 사전 활성화: [Week4 Step 5](<Week4-Step5 실습.md>)까지 완료한 상태에서 시작한다.

두 ClusterQueue를 Cohort에서 분리해 상대 팀의 유휴 quota를 전혀 빌리지 못하게 하고 공유, 부분 격리, 완전 격리 결과를 비교한다.

### 이전 Job과 LendingLimit 초기화
```bash
oc delete jobs -n gpu-team-a \
  -l app.kubernetes.io/name=week4-gpu-load --ignore-not-found
oc delete jobs -n gpu-team-b \
  -l app.kubernetes.io/name=week4-gpu-load --ignore-not-found

for CQ in gpu-team-a-cq gpu-team-b-cq; do
  oc patch clusterqueue "$CQ" --type=json \
    -p='[{"op":"remove","path":"/spec/resourceGroups/0/flavors/0/resources/0/lendingLimit"}]'
done
```

### Cohort에서 두 Queue 분리
```bash
for CQ in gpu-team-a-cq gpu-team-b-cq; do
  oc patch clusterqueue "$CQ" --type=json \
    -p='[{"op":"remove","path":"/spec/cohortName"}]'
done

oc get clusterqueue gpu-team-a-cq gpu-team-b-cq \
  -o custom-columns=NAME:.metadata.name,COHORT:.spec.cohortName
```

`COHORT`가 비어 있으면 두 Queue는 서로 quota를 빌려주지 않는다.

### Team A Job 4개 재제출
외부 YAML 대신 [Week4 Step 3의 Team A Job 4개 제출](<Week4-Step3 실습.md#team-a-job-4개-제출>)에 있는 heredoc 명령을 다시 실행한다.

```bash
oc get jobs -n gpu-team-a -w
```

Team B가 비어 있어도 Team A Job은 nominal quota 2개만 admission되고 나머지 2개는 suspend 상태로 대기해야 한다.

```bash
oc get workloads -n gpu-team-a
oc describe clusterqueue gpu-team-a-cq
```

### 격리 수준 비교
| 구성 | Team B가 유휴일 때 Team A admission | 특징 |
|---|---:|---|
| Cohort, limit 없음 | 4 | 활용률 최대, Team B 요청 시 빌린 workload 회수 |
| Cohort, `lendingLimit: 1` | 3 | Team B quota 1개 보존 |
| Cohort 없음 | 2 | 완전 quota 격리, 유휴 자원도 공유하지 않음 |

Time-Slicing의 GPU 메모리/장애 격리 수준은 세 구성 모두 동일하다. 위 표는 Kueue admission quota의 격리만 비교한다.

### 실습 리소스 정리
```bash
oc delete jobs -n gpu-team-a \
  -l app.kubernetes.io/name=week4-gpu-load --ignore-not-found
oc delete jobs -n gpu-team-b \
  -l app.kubernetes.io/name=week4-gpu-load --ignore-not-found

oc delete namespace gpu-team-a gpu-team-b --ignore-not-found
oc delete clusterqueue gpu-team-a-cq gpu-team-b-cq --ignore-not-found
oc delete cohort week4-gpu-cohort --ignore-not-found
oc delete resourceflavor week4-shared-gpu --ignore-not-found
oc delete workloadpriorityclass week4-borrower week4-owner \
  --ignore-not-found
```

Namespace와 LocalQueue, ConfigMap은 Namespace 삭제로 제거되고 ClusterQueue, Cohort, ResourceFlavor, WorkloadPriorityClass도 매니페스트 기준으로 제거된다.

### NVIDIA Device Plugin 설정 원복
사전점검에서 백업한 ClusterPolicy 설정과 node label을 복원한 뒤 Week4 ConfigMap을 삭제한다.

```bash
BEFORE_CONFIG=$(cat /tmp/week4-device-plugin-config-before.json)
if [ "$BEFORE_CONFIG" = "null" ]; then
  oc patch clusterpolicy gpu-cluster-policy --type=json \
    -p='[{"op":"remove","path":"/spec/devicePlugin/config"}]' || true
else
  oc patch clusterpolicy gpu-cluster-policy --type=merge \
    -p "{\"spec\":{\"devicePlugin\":{\"config\":$BEFORE_CONFIG}}}"
fi

BEFORE_LABEL=$(cat /tmp/week4-node-config-label-before)
if [ "$BEFORE_LABEL" = "__ABSENT__" ]; then
  oc label node ocp-w01-gpu nvidia.com/device-plugin.config-
else
  oc label node ocp-w01-gpu \
    nvidia.com/device-plugin.config="$BEFORE_LABEL" --overwrite
fi

oc delete configmap week4-gpu-sharing \
  -n nvidia-gpu-operator --ignore-not-found
```

### 최종 확인
```bash
oc get namespace gpu-team-a gpu-team-b
oc get cohort,clusterqueue,resourceflavor | grep week4
oc get workload -A | grep -E 'team-a-gpu|team-b-gpu'

oc get node ocp-w01-gpu \
  -o jsonpath='{.metadata.labels.nvidia\.com/device-plugin\.config}{"\n"}{.status.allocatable.nvidia\.com/gpu}{"\n"}'
```

앞의 세 명령은 `NotFound` 또는 빈 결과가 정상이다. 마지막 출력은 사전점검에서 백업한 label과 GPU capacity 상태로 돌아와야 한다. NFD, KMM, NVIDIA GPU Operator, Kueue Operator와 각 컨트롤러 CR은 삭제하지 않는다.
