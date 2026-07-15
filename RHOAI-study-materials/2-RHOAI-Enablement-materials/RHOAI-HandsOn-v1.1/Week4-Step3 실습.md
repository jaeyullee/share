# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 4 - Step 3 Team A의 유휴 quota 차용

> 사전 활성화: [Week4 Step 2](<Week4-Step2 실습.md>)의 Cohort와 팀별 Queue 구성이 필요하다.

Team B가 유휴 상태일 때 Team A가 자신의 nominal GPU 슬롯 2개와 Team B의 미사용 슬롯 2개를 함께 사용하는지 확인한다.

### Team A Job 4개 제출
```bash
oc apply -f /tmp/python3/manifests/week4-team-a-borrow.yaml
```

각 Job은 `nvidia.com/gpu: 1`을 요청한다. 단일 Job에 4를 요청하지 않는 이유는 두 가지다.

1. Time-Slicing에서 4를 요청해도 연산 성능을 4배 보장하지 않는다.
2. Kueue는 하나의 Workload를 4에서 2로 줄이지 않는다. 독립 Workload여야 빌린 슬롯 2개만 회수할 수 있다.

### Admission과 실행 확인
```bash
oc get jobs -n gpu-team-a -w
```

네 Job의 `SUSPEND`가 모두 `False`가 되면 `Ctrl+C`로 종료한다.

```bash
oc get pods -n gpu-team-a -o wide
oc get workloads -n gpu-team-a
oc describe clusterqueue gpu-team-a-cq
oc describe clusterqueue gpu-team-b-cq
```

Team A의 네 workload가 admission되고 GPU 사용량 4 중 2가 cohort에서 빌린 quota로 표시되어야 한다. 표시 형식은 Kueue 버전에 따라 `Borrowing`, `Usage` 또는 flavor/resource 표로 다를 수 있다.

### CUDA 부하 확인
```bash
for JOB in team-a-gpu-1 team-a-gpu-2 team-a-gpu-3 team-a-gpu-4; do
  oc logs -n gpu-team-a job/$JOB --tail=3
done

oc debug node/ocp-w01-gpu -- chroot /host nvidia-smi
```

각 로그에 RTX 5060 Ti와 CUDA 버전, 반복 횟수가 출력되고 `nvidia-smi`에 여러 Python process가 보여야 한다. Time-Slicing은 process별 메모리 또는 장애 격리를 제공하지 않는다.

### 관찰 결과
- Team A nominal quota: 2
- Team A admission workload: 4
- Team A 차용량: 2
- Team B workload: 0

Job은 다음 Step에서 회수 동작을 확인하기 위해 실행 상태로 둔다.
