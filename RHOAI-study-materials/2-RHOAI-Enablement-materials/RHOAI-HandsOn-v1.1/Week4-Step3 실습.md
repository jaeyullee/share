# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 4 - Step 3 Team A의 유휴 quota 차용

> 사전 활성화: [Week4 Step 2](<Week4-Step2 실습.md>)의 Cohort와 팀별 Queue 구성이 필요하다.

Team B가 유휴 상태일 때 Team A가 자신의 nominal GPU 슬롯 2개와 Team B의 미사용 슬롯 2개를 함께 사용하는지 확인한다.

### Team A Job 4개 제출
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: List
items:
  - apiVersion: batch/v1
    kind: Job
    metadata:
      name: team-a-gpu-1
      namespace: gpu-team-a
      labels: &job-labels
        app.kubernetes.io/name: week4-gpu-load
        week4.rhoai/team: a
        kueue.x-k8s.io/queue-name: team-lq
        kueue.x-k8s.io/priority-class: week4-borrower
    spec: &job-spec
      suspend: true
      backoffLimit: 0
      template:
        metadata:
          labels:
            app.kubernetes.io/name: week4-gpu-load
            week4.rhoai/team: a
        spec:
          restartPolicy: Never
          nodeSelector:
            lab-role: gpu
          containers:
            - name: gpu-load
              image: 192.168.10.50:5010/rhaii/vllm-cuda-rhel9:rhoai-3.4
              command: [python3, /opt/week4/gpu_share_load.py]
              env:
                - name: DURATION_SECONDS
                  value: "1800"
                - name: MATRIX_SIZE
                  value: "2048"
              resources:
                requests:
                  cpu: 250m
                  memory: 1Gi
                limits:
                  nvidia.com/gpu: "1"
              volumeMounts:
                - name: load-script
                  mountPath: /opt/week4
                  readOnly: true
          volumes:
            - name: load-script
              configMap:
                name: week4-gpu-load
  - apiVersion: batch/v1
    kind: Job
    metadata:
      name: team-a-gpu-2
      namespace: gpu-team-a
      labels: *job-labels
    spec: *job-spec
  - apiVersion: batch/v1
    kind: Job
    metadata:
      name: team-a-gpu-3
      namespace: gpu-team-a
      labels: *job-labels
    spec: *job-spec
  - apiVersion: batch/v1
    kind: Job
    metadata:
      name: team-a-gpu-4
      namespace: gpu-team-a
      labels: *job-labels
    spec: *job-spec
EOF
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

oc get clusterqueue gpu-team-a-cq -o json | jq -r '
  .status.flavorsUsage[]
  | .name as $flavor
  | .resources[]
  | select(.name == "nvidia.com/gpu")
  | "flavor=\($flavor) total=\(.total) borrowed=\(.borrowed)"
'
```

Team A의 네 Workload가 `ADMITTED=True`이고 다음 집계가 출력되어야 한다.

```text
flavor=week4-shared-gpu total=4 borrowed=2
```

`total=4`는 Team A가 예약한 전체 GPU 슬롯이고, `borrowed=2`는 자체 nominal quota 2를 초과해 같은 Cohort의 Team B에서 빌린 슬롯이다. 특정 Workload 두 개에 borrowed 표시가 붙는 것이 아니라 ClusterQueue 전체 사용량으로 집계된다.

### CUDA 부하 확인
```bash
for JOB in team-a-gpu-1 team-a-gpu-2 team-a-gpu-3 team-a-gpu-4; do
  oc logs -n gpu-team-a job/$JOB --tail=3
done

DRIVER_POD="$(
  oc get pods -n nvidia-gpu-operator \
    --field-selector spec.nodeName=ocp-w01-gpu -o name | \
    grep '^pod/nvidia-driver-daemonset-' | head -n1
)"
test -n "$DRIVER_POD"

oc exec -n nvidia-gpu-operator "$DRIVER_POD" \
  -c nvidia-driver-ctr -- nvidia-smi
```

RHCOS 호스트에는 일반 패키지 형태의 `nvidia-smi`가 없고 GPU Operator의 드라이버 컨테이너가 실행 파일을 제공한다. 각 Job 로그에 RTX 5060 Ti와 CUDA 버전, 반복 횟수가 출력되고, 드라이버 컨테이너에서 실행한 `nvidia-smi`에 여러 Python process가 보여야 한다. Time-Slicing은 process별 메모리 또는 장애 격리를 제공하지 않는다.

### 관찰 결과
- Team A nominal quota: 2
- Team A admission workload: 4
- Team A 차용량: 2
- Team B workload: 0

Job은 다음 Step에서 회수 동작을 확인하기 위해 실행 상태로 둔다.
