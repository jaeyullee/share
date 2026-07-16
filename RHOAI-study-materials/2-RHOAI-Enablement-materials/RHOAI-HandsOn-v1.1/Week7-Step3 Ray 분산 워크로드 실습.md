# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 7 - Step 3 Ray 분산 워크로드

> 사전 준비: [Week3 Day12](<Week3-Day12 실습.md>)에서 Red Hat build of Kueue를 설치하고 Kueue CR integration에 `RayJob`, `RayCluster`, `Pod`, `Deployment`가 있는지 확인한다.

RHOAI가 관리하는 KubeRay Operator와 외부 Red Hat build of Kueue를 연결해 head와 worker가 다른 노드에서 실행되는 RayJob을 제출한다. CodeFlare Operator를 별도로 설치하지 않는다.

### 현재 상태 백업과 Ray 활성화

```bash
oc get dsc default-dsc -o jsonpath='{.spec.components.ray.managementState}' \
  > /tmp/week7-ray-state-before

oc get kueues.kueue.openshift.io cluster -o json | jq '{
  managementState: .spec.managementState,
  integrations: .spec.config.integrations.frameworks
}'

oc patch dsc default-dsc --type=merge \
  -p '{"spec":{"components":{"ray":{"managementState":"Managed"}}}}'

oc get dsc default-dsc \
  -o jsonpath='{.status.conditions[?(@.type=="RayReady")]}{"\n"}'
oc wait deployment/kuberay-operator \
  -n redhat-ods-applications \
  --for=condition=Available --timeout=300s

oc get crd rayjobs.ray.io rayclusters.ray.io
```

`RayReady=True`와 KubeRay Operator `Available=True`를 확인한다.

### 전용 Queue 생성

```bash
oc new-project week7-ray
oc label namespace week7-ray kueue.openshift.io/managed=true --overwrite

oc apply -f - <<'EOF'
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata:
  name: week7-linux
spec:
  nodeLabels:
    kubernetes.io/os: linux
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: week7-ray-cq
spec:
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: week7-ray
  queueingStrategy: BestEffortFIFO
  resourceGroups:
    - coveredResources:
        - cpu
        - memory
      flavors:
        - name: week7-linux
          resources:
            - name: cpu
              nominalQuota: "2"
            - name: memory
              nominalQuota: 8Gi
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: week7-ray-lq
  namespace: week7-ray
spec:
  clusterQueue: week7-ray-cq
EOF

oc get resourceflavor week7-linux
oc get clusterqueue week7-ray-cq
oc get localqueue week7-ray-lq -n week7-ray
```

ResourceFlavor의 `kubernetes.io/os=linux`는 Kueue가 quota 예약과 함께 적용할 공통 노드 조건이다. head와 worker의 실제 노드 분리는 RayCluster Pod template의 `lab-role` selector로 지정한다.

### RayJob 제출

이 이미지는 현재 RHOAI 3.4 환경에서 Ray 2.53.0 실행을 검증한 CPU workbench image다. head memory request를 2Gi로 낮추면 초기화 중 OOM이 발생할 수 있으므로 3Gi를 사용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: ray.io/v1
kind: RayJob
metadata:
  name: week7-ray-demo
  namespace: week7-ray
  labels:
    kueue.x-k8s.io/queue-name: week7-ray-lq
spec:
  suspend: true
  shutdownAfterJobFinishes: true
  ttlSecondsAfterFinished: 300
  entrypoint: >-
    python -c "import ray;
    ray.init(address='auto');
    f=ray.remote(lambda x: (x, x*x));
    refs=[f.remote(i) for i in range(4)];
    print('week7-ray-ok', ray.get(refs))"
  rayClusterSpec:
    rayVersion: "2.53.0"
    headGroupSpec:
      rayStartParams:
        dashboard-host: "0.0.0.0"
      template:
        spec:
          nodeSelector:
            lab-role: cpu
          containers:
            - name: ray-head
              image: registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:d82680de0790b333892da2179c12225f5858f862b060964f2c62314cb23714fe
              resources:
                requests:
                  cpu: 500m
                  memory: 3Gi
                limits:
                  cpu: "2"
                  memory: 6Gi
    workerGroupSpecs:
      - groupName: week7-workers
        replicas: 1
        minReplicas: 1
        maxReplicas: 1
        rayStartParams: {}
        template:
          spec:
            nodeSelector:
              lab-role: gpu
            containers:
              - name: ray-worker
                image: registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:d82680de0790b333892da2179c12225f5858f862b060964f2c62314cb23714fe
                resources:
                  requests:
                    cpu: 500m
                    memory: 2Gi
                  limits:
                    cpu: "2"
                    memory: 4Gi
EOF
```

Kueue가 Workload quota를 예약하면 RayJob의 `suspend`를 해제하고 RayCluster를 만든다.

```bash
oc get rayjob,raycluster,workload -n week7-ray -w
```

다른 셸에서 Pod 배치 노드를 확인한다.

```bash
oc get pods -n week7-ray -o wide
oc get workload -n week7-ray -o yaml | \
  sed -n '/conditions:/,/resourceRequests:/p'
```

판정 기준은 다음과 같다.

- Workload: `QuotaReserved=True`, `Admitted=True`
- head Pod: `lab-role=cpu` 노드
- worker Pod: `lab-role=gpu` 노드
- RayJob: `jobStatus=SUCCEEDED`

```bash
oc wait rayjob/week7-ray-demo -n week7-ray \
  --for=jsonpath='{.status.jobStatus}'=SUCCEEDED --timeout=900s
oc logs -n week7-ray job/week7-ray-demo
```

예상 로그는 다음과 같다.

```text
week7-ray-ok [(0, 0), (1, 1), (2, 4), (3, 9)]
```

### 트러블슈팅

```bash
oc describe workload -n week7-ray
oc describe rayjob week7-ray-demo -n week7-ray
oc get events -n week7-ray --sort-by=.lastTimestamp | tail -30
oc logs deployment/kuberay-operator \
  -n redhat-ods-applications --tail=100
```

- `suspend=true` 유지: LocalQueue 이름, Kueue integration, ClusterQueue quota를 확인한다.
- `Insufficient cpu/memory`: Kueue admission 이후 Kubernetes Scheduler 단계의 노드 allocatable과 requests를 확인한다.
- head OOM: head request/limit를 3Gi/6Gi로 유지한다.
- image pull 실패: RHOAI workbench digest와 IDMS mirror 상태를 확인한다.

### 원복

Ray workload를 먼저 지운 뒤 component를 원래 상태로 되돌린다.

```bash
oc delete rayjob week7-ray-demo -n week7-ray --ignore-not-found
oc delete namespace week7-ray --wait=true
oc delete clusterqueue week7-ray-cq --ignore-not-found
oc delete resourceflavor week7-linux --ignore-not-found

RAY_STATE="$(cat /tmp/week7-ray-state-before)"
oc patch dsc default-dsc --type=merge \
  -p "$(jq -n --arg state "$RAY_STATE" \
  '{spec:{components:{ray:{managementState:$state}}}}')"

if [ "$RAY_STATE" = "Removed" ]; then
  oc wait --for=delete deployment/kuberay-operator \
    -n redhat-ods-applications --timeout=300s || true
  oc get rayjob,raycluster -A
  oc delete crd rayjobs.ray.io rayclusters.ray.io \
    --ignore-not-found
fi

rm -f /tmp/week7-ray-state-before
unset RAY_STATE
```

Ray CRD 삭제는 다른 Namespace에 `RayJob`이나 `RayCluster`가 없고 시작 상태가 `Removed`였을 때만 수행한다. DSC를 `Removed`로 되돌려도 CRD는 남을 수 있으므로 시작 상태까지 되돌릴 때 별도로 확인한다.

### 공식 문서

- [RHOAI 3.4 - Working with distributed workloads](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/working_with_distributed_workloads/working_with_distributed_workloads)
- [RHOAI 3.4 - Managing workloads with Kueue](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/managing_openshift_ai/managing-workloads-with-kueue)
