# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 4 - Step 4 Team B의 nominal quota 회수

> 사전 활성화: [Week4 Step 3](<Week4-Step3 실습.md>)의 Team A Job 4개가 실행 중이어야 한다.

Team B가 GPU Job 2개를 제출하면 자신의 nominal quota를 사용 중인 Team A의 차용 workload 2개를 회수하는지 확인한다.

### Team B Job 제출
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: List
items:
  - apiVersion: batch/v1
    kind: Job
    metadata:
      name: team-b-gpu-1
      namespace: gpu-team-b
      labels: &job-labels
        app.kubernetes.io/name: week4-gpu-load
        week4.rhoai/team: b
        kueue.x-k8s.io/queue-name: team-lq
        kueue.x-k8s.io/priority-class: week4-owner
    spec: &job-spec
      suspend: true
      backoffLimit: 0
      template:
        metadata:
          labels:
            app.kubernetes.io/name: week4-gpu-load
            week4.rhoai/team: b
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
      name: team-b-gpu-2
      namespace: gpu-team-b
      labels: *job-labels
    spec: *job-spec
EOF
```

두 ClusterQueue에는 `reclaimWithinCohort: Any`가 설정되어 있다. 따라서 Team B workload가 자신의 nominal quota 안에 들어오면 Kueue는 Team A가 Team B quota에서 빌려 실행 중인 workload를 회수할 수 있다.

### 회수와 재입장 대기 관찰
두 터미널에서 각각 확인하면 흐름을 보기 쉽다.

```bash
# 터미널 1
oc get workloads -A -w
```

```bash
# 터미널 2
oc get pods -n gpu-team-a -w
```

Team A의 네 workload 중 두 개가 eviction되고 관련 Pod가 종료된다. 해당 Job은 삭제되는 것이 아니라 다시 suspend되거나 재입장을 기다린다. 이후 Team B Job 2개가 admission되어 실행된다.

### 최종 상태 확인
```bash
oc get jobs -n gpu-team-a
oc get jobs -n gpu-team-b
oc get workloads -n gpu-team-a
oc get workloads -n gpu-team-b

oc describe clusterqueue gpu-team-a-cq
oc describe clusterqueue gpu-team-b-cq

oc get events -n gpu-team-a --sort-by=.lastTimestamp | tail -30
oc get events -n gpu-team-b --sort-by=.lastTimestamp | tail -30
```

예상 상태는 다음과 같다.

| 팀 | 실행 GPU Job | 설명 |
|---|---:|---|
| Team A | 2 | 자신의 nominal quota 2개 사용 |
| Team B | 2 | 자신의 nominal quota 2개 회수 후 사용 |

`week4-owner`의 높은 우선순위는 workload 성격을 명확히 하지만, 이 단계의 핵심 회수 조건은 Team B가 자기 nominal quota를 요구하고 `reclaimWithinCohort: Any`가 설정된 것이다.

### 선점 이벤트 확인
```bash
oc describe workload -n gpu-team-a | \
  grep -Ei 'Evict|Preempt|Requeue|Admitted|Reason' -A2
```

Kueue 버전에 따라 `Preempted`, `Evicted`, `Requeued` 조건이나 이벤트 이름이 다를 수 있다. Pod가 임의 장애로 죽은 것이 아니라 quota 회수 때문에 종료되었다는 점을 확인한다.
