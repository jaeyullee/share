# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 4 - Step 5 LendingLimit으로 부분 격리

> 사전 활성화: [Week4 Step 2](<Week4-Step2 실습.md>)의 두 ClusterQueue가 같은 Cohort에 있어야 한다.

각 팀이 유휴 nominal quota 중 최대 1개만 다른 팀에 빌려주도록 제한한다. Team A가 Job 4개를 제출해도 자신의 2개와 Team B가 빌려주는 1개, 총 3개만 admission되는지 확인한다.

### 이전 Job 초기화
```bash
oc delete jobs -n gpu-team-a \
  -l app.kubernetes.io/name=week4-gpu-load --ignore-not-found
oc delete jobs -n gpu-team-b \
  -l app.kubernetes.io/name=week4-gpu-load --ignore-not-found

oc wait --for=delete pod \
  -l app.kubernetes.io/name=week4-gpu-load \
  -n gpu-team-a --timeout=120s
oc wait --for=delete pod \
  -l app.kubernetes.io/name=week4-gpu-load \
  -n gpu-team-b --timeout=120s
```

### LendingLimit 설정
배열 전체가 예기치 않게 바뀌지 않도록 JSON Patch로 정확한 resource 항목에 필드를 추가한다.

```bash
for CQ in gpu-team-a-cq gpu-team-b-cq; do
  oc patch clusterqueue "$CQ" --type=json \
    -p='[{"op":"add","path":"/spec/resourceGroups/0/flavors/0/resources/0/lendingLimit","value":1}]'
done

oc get clusterqueue gpu-team-a-cq gpu-team-b-cq -o yaml | \
  grep -E 'name: nvidia.com/gpu|nominalQuota|lendingLimit'
```

`lendingLimit: 1`은 각 Queue가 자기 nominal quota 2개 중 최소 1개를 유휴 상태로 보존한다는 뜻이다. 빌리는 쪽의 상한을 직접 제한하려면 `borrowingLimit`을 사용한다.

### Team A Job 4개 재제출
외부 YAML 대신 [Week4 Step 3의 Team A Job 4개 제출](<Week4-Step3 실습.md#team-a-job-4개-제출>)에 있는 heredoc 명령을 다시 실행한다.

```bash
oc get jobs -n gpu-team-a -w
```

세 Job이 `SUSPEND=False`가 되고 한 Job은 `True`로 대기해야 한다.

```bash
oc get workloads -n gpu-team-a
oc describe clusterqueue gpu-team-a-cq
oc describe clusterqueue gpu-team-b-cq
```

예상 결과는 Team A nominal 2 + Team B 대여 허용 1 = admission 3이다.

### 리소스 이름 분리와의 차이
이 실습의 부분 격리는 **quota 수량**을 제한한다. `renameByDefault: true`를 사용해도 NVIDIA Device Plugin이 만드는 이름은 `nvidia.com/gpu.shared` 하나뿐이며, Time-Slicing용과 MPS용 임의 리소스명을 한 노드에 동시에 만들지 않는다.

공유 방식 자체를 분리하려면 GPU 노드를 둘 이상 준비해 노드별로 Time-Slicing 또는 MPS를 적용하고, 서로 다른 node label과 ResourceFlavor로 Queue를 분리해야 한다.

Job은 Step 6에서 격리 수준을 비교하기 위해 실행 상태로 둔다.
