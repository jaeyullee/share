# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 7 - Step 8 사용자 리소스 할당과 클러스터 확장

> **환경별 재확인**: platform type과 Machine API 제공 여부에 따라 MachineSet scale-out 또는 Agent ISO 경로가 달라진다. 문서의 `platform=None` 결과를 다른 클러스터에 그대로 적용하지 않는다. 공통 경계 조건은 [실습자료 검토 항목](<00-실습자료-검토항목.md#환경별-재확인>)을 참고한다.

> 사전 준비: [Week2 Day9](<Week2-Day9 실습.md>)의 프로젝트 RBAC·ResourceQuota와 [Week3 Day12](<Week3-Day12 실습.md>)의 Kueue quota 차이를 복습한다.

Namespace ResourceQuota와 LimitRange로 사용자 workload의 상한과 기본 request를 제어하고, 현재 클러스터가 MachineSet scale-out 대상인지 Agent ISO worker 추가 대상인지 판정한다.

### 클러스터 용량 기준선

```bash
oc get nodes -o custom-columns='NAME:.metadata.name,CPU:.status.allocatable.cpu,MEMORY:.status.allocatable.memory,GPU:.status.allocatable.nvidia\.com/gpu'
oc adm top nodes

for node in $(oc get node -o name); do
  echo "===== ${node} ====="
  oc describe "$node" | sed -n '/Allocated resources:/,/Events:/p'
done
```

`oc adm top`은 실제 사용량이고 `Allocated resources`는 Pod requests/limits 합계다. Scheduler와 Kueue admission 문제는 실제 CPU 사용률이 낮아도 requests 합계 때문에 발생할 수 있다.

### ResourceQuota와 LimitRange 생성

```bash
oc new-project week7-capacity

oc apply -f - <<'EOF'
apiVersion: v1
kind: ResourceQuota
metadata:
  name: week7-team-quota
  namespace: week7-capacity
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 2Gi
    limits.cpu: "4"
    limits.memory: 4Gi
    pods: "4"
    requests.storage: 5Gi
---
apiVersion: v1
kind: LimitRange
metadata:
  name: week7-team-defaults
  namespace: week7-capacity
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 250m
        memory: 256Mi
      default:
        cpu: 500m
        memory: 512Mi
      min:
        cpu: 50m
        memory: 64Mi
      max:
        cpu: "2"
        memory: 2Gi
EOF

oc describe resourcequota week7-team-quota -n week7-capacity
oc describe limitrange week7-team-defaults -n week7-capacity
```

### 정상 workload와 quota 초과 비교

resource를 생략한 정상 Job에는 LimitRange 기본값이 주입된다.

```bash
oc apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: week7-small
  namespace: week7-capacity
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: work
          image: registry.redhat.io/ubi9/nginx-126@sha256:10a020f93a6a0c59f0c8d16d3f1cfb7863579dbba847c9ab8bad9fa678a78d1c
          command: [/bin/sh, -c]
          args:
            - echo week7-small-ok
EOF

oc get pod -n week7-capacity -l job-name=week7-small \
  -o json | jq '.items[0].spec.containers[0].resources'
oc wait job/week7-small -n week7-capacity \
  --for=condition=Complete --timeout=300s
oc logs job/week7-small -n week7-capacity
```

CPU 3개와 memory 3Gi를 요청하는 Pod는 LimitRange의 container max를 초과하므로 API admission에서 바로 거부돼야 한다.

```bash
if oc apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: week7-oversized
  namespace: week7-capacity
spec:
  restartPolicy: Never
  containers:
    - name: work
      image: registry.redhat.io/ubi9/nginx-126@sha256:10a020f93a6a0c59f0c8d16d3f1cfb7863579dbba847c9ab8bad9fa678a78d1c
      command: [/bin/sh, -c]
      args:
        - echo should-not-run
      resources:
        requests:
          cpu: "3"
          memory: 3Gi
        limits:
          cpu: "3"
          memory: 3Gi
EOF
then
  echo 'ERROR: oversized Pod was unexpectedly accepted'
else
  echo 'EXPECTED: LimitRange rejected the Pod'
fi
```

출력에 `maximum cpu usage per Container is 2`와 `maximum memory usage per Container is 2Gi`가 표시된다. `Job`을 사용하면 Job 객체는 먼저 생성되고 Job controller가 Pod를 생성하는 시점에 거부되므로, 여기서는 admission 결과를 명확히 보기 위해 Pod를 직접 생성한다.

이번에는 LimitRange max 이내인 Pod 하나로 Namespace의 CPU·memory request quota를 모두 사용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: week7-quota-fill
  namespace: week7-capacity
spec:
  restartPolicy: Never
  containers:
    - name: work
      image: registry.redhat.io/ubi9/nginx-126@sha256:10a020f93a6a0c59f0c8d16d3f1cfb7863579dbba847c9ab8bad9fa678a78d1c
      command: [/bin/sh, -c]
      args:
        - sleep 300
      resources:
        requests:
          cpu: "2"
          memory: 2Gi
        limits:
          cpu: "2"
          memory: 2Gi
EOF

oc wait pod/week7-quota-fill -n week7-capacity \
  --for=condition=Ready --timeout=300s
oc describe resourcequota week7-team-quota -n week7-capacity
```

`Used`의 `requests.cpu=2`, `requests.memory=2Gi`를 확인한 뒤 작은 Pod를 하나 더 생성하면 집계 quota 초과로 거부된다.

```bash
if oc apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: week7-over-quota
  namespace: week7-capacity
spec:
  restartPolicy: Never
  containers:
    - name: work
      image: registry.redhat.io/ubi9/nginx-126@sha256:10a020f93a6a0c59f0c8d16d3f1cfb7863579dbba847c9ab8bad9fa678a78d1c
      command: [/bin/sh, -c]
      args:
        - echo should-not-run
      resources:
        requests:
          cpu: 250m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 512Mi
EOF
then
  echo 'ERROR: over-quota Pod was unexpectedly accepted'
else
  echo 'EXPECTED: ResourceQuota rejected the Pod'
fi

oc describe resourcequota week7-team-quota -n week7-capacity
oc get events -n week7-capacity --sort-by=.lastTimestamp | tail -20
```

출력에는 `exceeded quota: week7-team-quota`와 현재 used·limited 값이 표시된다. 이 실패는 Kueue의 admission 대기와 다르다. ResourceQuota와 LimitRange는 Pod API create를 거부하고, Kueue는 생성된 workload를 queue에서 대기시킨다.

### 확장 방식 판정

```bash
oc get infrastructure cluster -o json | jq '{
  platform: .status.platform,
  controlPlaneTopology: .status.controlPlaneTopology,
  infrastructureTopology: .status.infrastructureTopology
}'
oc get machineset -n openshift-machine-api
oc adm node-image create --help | sed -n '1,35p'
```

검증 환경은 `platform=None`이고 MachineSet이 없다. 따라서 `oc scale machineset`은 적용 대상이 아니다. OCP 4.22의 on-premise node image 기능으로 ISO를 만들고 새 VM 또는 bare-metal host를 boot하는 경로를 사용한다.

실제 worker 추가 시의 운영 순서는 다음과 같다.

1. 새 host의 CPU, memory, disk, MAC, 고정 IP, DNS, NTP, registry route를 준비한다.
2. 기존 cluster에 로그인한 `oc`와 registry credential로 node ISO를 생성한다.
3. 새 host를 ISO로 boot하고 preflight 결과를 확인한다.
4. client CSR의 node identity를 검증해 승인한다.
5. 이어서 생성되는 serving CSR을 다시 검증해 승인한다.
6. Node `Ready`, MachineConfigPool `Updated`, cluster operator 상태를 확인한다.
7. 필요한 `lab-role`, GPU, workload role label과 taint를 적용한다.

단일 노드 추가의 명령 골격은 다음과 같다. 실제 MAC, hostname, SSH key, registry config가 준비된 경우에만 실행한다.

```bash
mkdir -p /tmp/week7-node-image

oc adm node-image create \
  --dir=/tmp/week7-node-image \
  --mac-address='<NEW_NODE_MAC>' \
  --hostname='<NEW_NODE_HOSTNAME>' \
  --ssh-key-path='<SSH_PUBLIC_KEY_PATH>' \
  --registry-config='<PULL_SECRET_PATH>'

oc adm node-image monitor --ip-addresses '<NEW_NODE_IP>'
```

CSR은 무조건 일괄 승인하지 말고 requestor와 subject가 새 node와 일치하는지 확인한다.

```bash
oc get csr
oc get csr <CLIENT_CSR> -o yaml
oc adm certificate approve <CLIENT_CSR>

oc get csr
oc get csr <SERVING_CSR> -o yaml
oc adm certificate approve <SERVING_CSR>

oc get node -o wide
oc get machineconfigpool
oc get clusteroperator
```

### 운영 용량 판단

- 사용자 증가: Namespace quota와 Kueue ClusterQueue quota를 팀 단위로 분리한다.
- workload pending: API quota, Kueue admission, Scheduler 순서로 병목 계층을 구분한다.
- GPU serving 증가: GPU node pool과 CPU controller pool을 분리하고 taint/toleration을 설계한다.
- requests 포화: 실제 사용량만 보고 VM vCPU를 overcommit하지 말고 장애 시 동시 부하와 hypervisor 여유를 함께 본다.
- SNO 확장: worker를 추가해도 control plane은 SingleReplica이므로 control plane HA가 생기지 않는다.

### 원복

```bash
oc delete namespace week7-capacity --wait=true --ignore-not-found
rm -rf /tmp/week7-node-image
```

이 실습에서는 새 node를 실제 추가하지 않으므로 cluster node 구성 변경은 없다.

### 공식 문서

- [OpenShift 4.22 - Adding worker nodes](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/postinstallation_configuration/post-install-cluster-tasks)
- [OpenShift 4.22 - Worker nodes for single-node clusters](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/nodes/worker-nodes-for-single-node-openshift-clusters)
- [OpenShift 4.22 - Resource quotas per project](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/building_applications/quotas)
