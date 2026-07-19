# 오퍼레이터 설치

> **환경별 재확인**: OCP/RHOAI 버전, mirror registry 주소, CatalogSource, StorageClass, node label과 네트워크 경로는 검증 환경 값이다. 다른 클러스터에서는 대응 값을 먼저 확인한다. 공통 경계 조건은 [실습자료 검토 항목](<00-실습자료-검토항목.md#환경별-재확인>)을 참고한다.

## 오퍼레이터 준비/미러링 (disconnected 검증 환경 기준, 기능별 설치는 해당 Day에서 진행)

공식 문서: [Deploy OpenShift AI in a disconnected environment](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/installing_and_uninstalling_openshift_ai_self-managed_in_a_disconnected_environment/)

```yaml
operators:
  # Red Hat catalog
  - catalog: registry.redhat.io/redhat/redhat-operator-index:v4.22
    packages:
      # RHOAI base
      - name: rhods-operator
        channels:
          - name: stable-3.x
            minVersion: 3.4.0
            maxVersion: 3.4.0
      - name: openshift-cert-manager-operator
        channels:
          - name: stable-v1

      # RHOAI trainer / queue / distributed inference dependencies
      - name: job-set
        channels:
          - name: stable-v1.0
      - name: kueue-operator
        channels:
          - name: stable-v1.3
      - name: leader-worker-set
        channels:
          - name: stable-v1.0

      # API gateway / MaaS / policy candidates
      # RHCL 1.4.1 설치 시 아래 네 package가 함께 필요하다.
      # OCP 기본 openshift-dns-operator와 여기의 dns-operator는 서로 다른 제품이다.
      - name: rhcl-operator
        channels:
          - name: stable
            minVersion: 1.4.1
            maxVersion: 1.4.1
      - name: dns-operator
        channels:
          - name: stable
            minVersion: 1.4.0
            maxVersion: 1.4.0
      - name: authorino-operator
        channels:
          - name: stable
            minVersion: 1.4.1
            maxVersion: 1.4.1
      - name: limitador-operator
        channels:
          - name: stable
            minVersion: 1.4.0
            maxVersion: 1.4.0

      # MLOps / operations
      - name: openshift-pipelines-operator-rh
        channels:
          - name: latest
      - name: openshift-gitops-operator
        channels:
          - name: latest
      - name: redhat-oadp-operator
        channels:
          - name: stable

      # GPU worker support.
      - name: nfd
        channels:
          - name: stable
      - name: kernel-module-management
        channels:
          - name: stable

      # Optional local SSD storage/cache test.
      # GPU worker에 600G 빈 디스크(/dev/sdb)가 있으므로 모델 cache/PVC 성능 테스트에는 유효하다.
      # 단, 기본 RHOAI PVC는 TrueNAS NFS CSI를 계속 사용하고 LVMS는 별도 StorageClass로 둔다.
      - name: lvms-operator
        channels:
          - name: stable-4.22

      # Service Mesh 3 / mesh observability
      # servicemeshoperator3는 default channel이 stable이므로 stable-3.3만 남기면 oc-mirror가 실패한다.
      # 3.3 고정 설치를 원하더라도 stable과 stable-3.3을 함께 포함한다.
      # 3.3.1 버전을 포함할 경우 DSC가 필요로 하는 추가 이미지가 포함됨.
      - name: servicemeshoperator3
        channels:
          - name: stable
            minVersion: 3.3.5
            maxVersion: 3.3.1
          - name: stable-3.3
            minVersion: 3.3.5
            maxVersion: 3.3.1
      - name: kiali-ossm
        channels:
          - name: stable
            minVersion: 2.22.6
            maxVersion: 2.22.6
      - name: tempo-product
        channels:
          - name: stable
      - name: opentelemetry-product
        channels:
          - name: stable

  # Certified catalog
  - catalog: registry.redhat.io/redhat/certified-operator-index:v4.22
    packages:
      - name: gpu-operator-certified
        channels:
          - name: v26.3
```

### 미러 완료 판정 시 주의사항

#### NVIDIA GPU Operator: bundle과 operand 이미지를 따로 확인

`gpu-operator-certified` package와 `gpu-operator-bundle`이 미러에 있다고 해서 GPU Operator 설치에 필요한 이미지가 모두 준비된 것은 아니다.

| 구분 | 주요 source | 용도 |
|---|---|---|
| Operator catalog/bundle | `registry.redhat.io`, `registry.connect.redhat.com/nvidia` | OLM이 Subscription과 CSV를 설치할 때 사용 |
| GPU operand | `nvcr.io/nvidia` | driver, device plugin, container toolkit, DCGM, validator 실행에 사용 |

특히 bundle signature 오류를 우회하려고 bundle만 `additionalImages`와 `--remove-signatures`로 다시 미러하면, bundle의 `relatedImages`를 따라가는 Operator catalog 처리 과정이 생략될 수 있다. Bundle digest 확인만으로 미러 작업을 완료 처리하지 않는다.

본 커리큘럼의 disconnected 검증 환경에서 실제 pull이 확인된 operand repository는 다음과 같다.

```text
nvcr.io/nvidia/gpu-operator
nvcr.io/nvidia/driver
nvcr.io/nvidia/k8s-device-plugin
nvcr.io/nvidia/k8s/container-toolkit
nvcr.io/nvidia/k8s/dcgm-exporter
nvcr.io/nvidia/cloud-native/dcgm
nvcr.io/nvidia/cloud-native/k8s-driver-manager
```

이미지를 mirror registry에 복사하는 작업과 클러스터가 mirror를 사용하게 하는 작업은 별개다.

1. GPU Operator CSV의 `relatedImages`와 실제 ClusterPolicy operand가 참조하는 이미지를 mirror registry에 복사한다.
2. `registry.connect.redhat.com/nvidia` bundle과 `nvcr.io/nvidia/...` operand repository에 맞는 IDMS를 적용한다.
3. operand가 `tag@digest`를 사용하므로 ITMS만 확인하지 말고 IDMS의 source repository가 정확히 일치하는지 확인한다.
4. ClusterPolicy 생성 후 모든 operand Pod가 `Ready`이고 외부 registry pull 시도가 없는 상태까지 확인한다.

```bash
# 적용된 mirror 규칙 확인
oc get imagedigestmirrorset \
  idms-nvidia-connect-addon \
  idms-nvidia-gpu-operator-addon \
  idms-nvidia-nvcr-addon -o yaml

# 각 노드에 최종 생성된 CRI-O mirror 규칙 확인
oc debug node/ocp-w01-gpu -- chroot /host \
  cat /etc/containers/registries.conf

# GPU Operator 설치 후 최종 판정
oc get clusterpolicy
oc get pods -n nvidia-gpu-operator
oc get events -n nvidia-gpu-operator --sort-by=.lastTimestamp | tail -30
```

IDMS는 image를 복사하지 않는다. 위 IDMS가 존재해도 대상 mirror repository에 동일 digest가 없으면 설치는 실패한다.

#### RHCL: dependent package를 명시적으로 함께 미러

RHCL 1.4.1의 실제 OLM dependency resolution에서 다음 조합이 필요했다.

| 역할 | Package | 검증 버전 |
|---|---|---:|
| Connectivity Link 본체 | `rhcl-operator` | 1.4.1 |
| RHCL DNS 관리 | `dns-operator` | 1.4.0 |
| 인증·인가 | `authorino-operator` | 1.4.1 |
| Rate limit | `limitador-operator` | 1.4.0 |

`dns-operator`는 OCP 설치 시 기본으로 존재하는 `openshift-dns-operator`를 대체하는 Operator가 아니다. 이름이 비슷하지만 RHCL이 OLM dependency로 요구하는 별도 package이므로 OCP DNS가 정상이어도 미러에서 제외하면 안 된다.

축소형 `oc-mirror` ImageSet에 `rhcl-operator`만 적었다고 dependent package가 자동 추가된다고 가정하지 않는다. 네 package와 related image가 모두 복사됐는지 확인하고, 실제 Subscription resolution까지 성공해야 완료다.

```bash
# Catalog package 노출 확인
for package in rhcl-operator dns-operator authorino-operator limitador-operator; do
  oc get packagemanifest "$package" -n openshift-marketplace
done

# RHCL 설치 시 dependency resolution 확인
oc get subscription,installplan,csv -n openshift-operators
oc get events -n openshift-operators --sort-by=.lastTimestamp | tail -50
```

`oc-mirror`의 image copy 성공 건수나 CatalogSource `READY`만으로는 dependency 설치 성공을 보장하지 않는다. 최종 완료 조건은 RHCL Subscription이 네 package를 해석하고 관련 CSV가 모두 `Succeeded`가 되는 것이다.

### 당초 검토했다가 제외한 미러 대상

아래 항목은 "있으면 좋다"가 아니라 검증 환경에서 실제 검증 가능한지 기준으로 제외했다. 하드웨어나 테스트 목표가 바뀌면 다시 포함한다.
| Package | 제외 이유 |
|---|---|
| `odf-operator` | 단일 홈서버 환경에서 리소스 부담이 크고, 현재 PVC/S3는 TrueNAS NFS CSI/S3로 대체한다. |
| `sriov-network-operator` | SR-IOV capable NIC/VF 설계가 검증 환경에 없다. |
| `nvidia-network-operator` | Mellanox/ConnectX, RDMA/RoCE, GPUDirect RDMA 환경이 아니다. |
| `ibm-spyre-operator` | IBM Spyre 가속기 하드웨어가 없다. |
| `kuadrant-operator` | community catalog 쪽 deprecated 가능성이 있어 RHCL + DNS + Authorino + Limitador 경로를 우선한다. |
| `openshift-serverless-operator` | RHOAI 3.4 기본 서빙은 KServe RawDeployment 기준이고, KServe Serverless deployment mode는 deprecated다. |
| `metallb-operator` | 검증 환경은 Bastion HAProxy/DNS와 VM 내부망으로 구성했다. 별도 LoadBalancer 실습 때만 포함한다. |



## 오퍼레이터 설치 순서

### Red Hat OpenShift AI 오퍼레이터 설치

공식 문서: [Installing and deploying OpenShift AI](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/installing_and_uninstalling_openshift_ai_self-managed/installing-and-deploying-openshift-ai_install)
1. cert-manager 오퍼레이터 설치

2. Job Set Operator > JobSetOperator 인스턴스 생성

3. image.config.openshift.io/cluster.spec.additionalTrustedCA에 registry CA ConfigMap을 연결

4. StorageClass 구성 및 default storageclass 지정

5. (Servicemesh3 오퍼레이터 미러 시 3.3.1 제외한 경우만)RHOAI의 DSCInitialization 인스턴스가 생성하는 gateway pod에 필요한 이미지 pull. RHOAI 버전에 따라 확인 필요
```yaml
kind: ImageSetConfiguration
apiVersion: mirror.openshift.io/v2alpha1
mirror:
  additionalImages:
  - name: registry.redhat.io/openshift-service-mesh/istio-pilot-rhel9@sha256:4813bf7ae960860d28b5ab7b493ce10f1879e3276b1b64732299a9750737bcfd
  - name: registry.redhat.io/openshift-service-mesh/istio-proxyv2-rhel9@sha256:bc34f81266d8b0d2f5a8e71e966098d4edef70ac8dbb077a014a27fe1b71ec0a
```

6. red hat openshift ai 오퍼레이터 설치 > DataScienceCluster 인스턴스 생성
```yaml
spec:
  components:
    sparkoperator:
      managementState: Removed              # Spark 기반 분산 데이터 처리/파이프라인 실행 기능 사용 여부
    kserve:
      managementState: Managed              # RawDeployment 기반 모델 서빙 기능 사용 여부
      modelsAsService:
        managementState: Removed            # RHOAI MaaS/LLMInferenceService 계열 기능 사용 여부
      nim:
        airGapped: false                    # NIM 사용 시 air-gapped 동작 여부. true면 외부 API 호출과 NIM 모델 목록 ConfigMap 생성을 건너뛰는 disconnected 전용 동작
        managementState: Removed            # NVIDIA NIM 연동 기능 사용 여부
      rawDeploymentServiceConfig: Headless  # RawDeployment InferenceService의 Service 형태. Headless는 ClusterIP None, Headed는 일반 ClusterIP Service를 만들도록 KServe 설정
      wva:
        managementState: Removed            # Workload/virtual assistant 계열 부가 기능 사용 여부
    modelregistry:
      managementState: Managed              # Model Registry/Model Catalog 기능 사용 여부
      registriesNamespace: rhoai-model-registries
    feastoperator:
      managementState: Removed              # Feast Feature Store 기능 사용 여부. 
    trustyai:
      eval:
        lmeval:
          permitCodeExecution: deny         # LMEval 평가 중 평가 코드가 임의 코드 실행을 할 수 있는지 제어. 보안/재현성을 위해 기본 deny
          permitOnline: deny                # LMEval 평가 중 외부 온라인 접근을 허용할지 제어. disconnected 전제와 재현 가능한 평가를 위해 deny
      managementState: Managed              # TrustyAI/guardrails/eval 관련 기능 사용 여부
      mcpGuardrailsMode: false
    aipipelines:
      argoWorkflowsControllers:
        managementState: Managed            # Data Science Pipelines 실행 엔진인 bundled Argo Workflows controller를 RHOAI가 관리. ArgoCD 와 다름
      managementState: Managed              # Data Science Pipelines 기능 사용 여부
    ray:
      managementState: Removed              # Ray/CodeFlare 분산 워크로드 기능 사용 여부
    kueue:
      defaultClusterQueueName: default
      defaultLocalQueueName: default
      managementState: Removed              # Kueue 연동 여부. Red Hat build of Kueue Operator 로 기능 사용할거라면 Unmanaged로 설정.
    workbenches:
      managementState: Managed              # Jupyter/Code Server Workbench 기능 사용 여부
      workbenchNamespace: rhods-notebooks
    mlflowoperator:
      managementState: Managed              # MLflow 관련 실습/추적 기능 사용 여부
    dashboard:
      managementState: Managed              # RHOAI 웹 콘솔 기능 사용 여부
    trainer:
      managementState: Managed              # RHOAI Trainer/Kubeflow Trainer 계열 학습 Job 기능 사용 여부
    llamastackoperator:
      managementState: Removed              # Llama Stack 서버/배포 생명주기 관리 기능. RAG/agentic AI/OpenAI-compatible API 사용 시 활성화
    trainingoperator:
      managementState: Removed              # Kubeflow Trainer 계열 기능 사용 여부
```

7. (rh-ai 콘솔 접속 실패하는 경우에만. 403 status) 네트워크 폴리시 추가
```bash
oc apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kube-auth-proxy-allow-egress
  namespace: openshift-ingress
  annotations:
    createdBy: manual
    reason: "Allow RHOAI Gateway kube-auth-proxy to reach OpenShift OAuth/Kubernetes API
    under openshift-ingress deny-all policy."
spec:
  podSelector:
    matchLabels:
      app: kube-auth-proxy
  policyTypes:
    - Egress
  egress:
    - {}
EOF

## 검증
oc get networkpolicy -n openshift-ingress kube-auth-proxy-allow-egress
oc logs -n openshift-ingress deploy/kube-auth-proxy --tail=50
curl -k -I https://rh-ai.apps.sno.ocp422.com/
```

### 9020 포트로 서비스하는 minio 준비 및 5010 포트로 서비스하는 model image registry 준비

### OVN-Kubernetes routingViaHost와 storage NIC forwarding 구성

공식 문서: [OVN-Kubernetes gateway와 egress routing policy](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/ovn-kubernetes_network_plugin/index), [Node Tuning Operator 사용](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/scalability_and_performance/using-node-tuning-operator)

**목적**: Pod가 외부 주소에 접근할 때 노드의 Linux routing table을 사용하게 한다. 검증 환경에서는 `192.168.20.0/24`가 storage NIC `enp6s19`, `192.168.10.0/24`와 기본 경로가 `br-ex`를 사용하므로 S3와 Nexus/Gitea 경로를 목적지별로 분리할 수 있다.

`routingViaHost`는 cluster-wide 설정이다. 특정 Namespace만 선택하는 EgressIP와 달리 모든 Pod의 외부 egress가 host routing stack을 사용한다. OVS hardware offload를 사용할 때 필요한 `routingViaHost=false`와는 양립하지 않으므로 SmartNIC offload 도입 시 설계를 다시 검토한다.

1. 기존 설정을 백업하고 `routingViaHost=true`로 전환한다.

```bash
oc get network.operator.openshift.io cluster -o yaml \
  > network-operator-before-routing-via-host.yaml

oc patch network.operator.openshift.io cluster --type=merge \
  -p '{"spec":{"defaultNetwork":{"ovnKubernetesConfig":{"gatewayConfig":{"routingViaHost":true}}}}}'

oc rollout status daemonset/ovnkube-node \
  -n openshift-ovn-kubernetes --timeout=5m

oc get clusteroperator network
oc get network.operator.openshift.io cluster -o yaml | \
  grep -A 5 gatewayConfig
```

Network Operator가 `Available=True`, `Progressing=False`, `Degraded=False`인지 확인한 뒤 다음 단계로 진행한다.

2. storage NIC가 있는 노드에 전용 label을 지정한다.

```bash
oc label node ocp-w01-gpu ocp-w02-cpu sno-node \
  network.openshift.io/storage-route=true --overwrite
```

3. storage NIC에만 IPv4 forwarding을 활성화한다. `routingViaHost=true`만으로 보조 NIC `enp6s19`의 forwarding이 자동 활성화되지 않았으므로 Node Tuning Operator로 좁게 적용한다. `gatewayConfig.ipForwarding: Global`은 사용하지 않는다.

```bash
oc apply -f <<'EOF'
apiVersion: tuned.openshift.io/v1
kind: Tuned
metadata:
  name: routing-via-host-storage-forwarding
  namespace: openshift-cluster-node-tuning-operator
spec:
  profile:
    - name: routing-via-host-storage-forwarding
      data: |
        [main]
        summary=Enable IPv4 forwarding on the storage NIC for routingViaHost
        include=openshift-node

        [sysctl]
        net.ipv4.conf.enp6s19.forwarding=1
  recommend:
    - match:
        - label: network.openshift.io/storage-route
          value: "true"
      priority: 20
      profile: routing-via-host-storage-forwarding
EOF
```

4. 기존 EgressIP 방식에서 전환하는 경우 EgressIP CR, Namespace selector label, 기존 node label과 Tuned를 제거한다. 신규 Tuned가 노드에 적용된 것을 먼저 확인해야 S3 경로가 끊기지 않는다.

```bash
oc get profile.tuned.openshift.io \
  -n openshift-cluster-node-tuning-operator \
  -o custom-columns=NODE:.metadata.name,PROFILE:.status.tunedProfile

oc delete egressip s3-storage-egress --ignore-not-found
oc label namespace jukebox network-zone-
oc label node ocp-w01-gpu ocp-w02-cpu \
  k8s.ovn.org/egress-assignable-
oc delete tuned s3-egressip-forwarding \
  -n openshift-cluster-node-tuning-operator --ignore-not-found
```

5. Workbench에서 storage망과 service망을 검증한다.

```bash
oc exec -n jukebox jukebox-workbench-0 -c jukebox-workbench -- \
  curl -fsS http://192.168.20.5:9000/minio/health/live

oc exec -n jukebox jukebox-workbench-0 -c jukebox-workbench -- \
  curl -kfsSL -o /dev/null -w '%{http_code}\n' \
  http://gitea.apps.sno.ocp422.com/

oc exec -n jukebox jukebox-workbench-0 -c jukebox-workbench -- \
  curl -fsSL -o /dev/null -w '%{http_code}\n' \
  http://192.168.10.50:8081/
```

2026-07-14 검증에서는 세 노드 모두 `routing-via-host-storage-forwarding` profile이 적용됐고 Workbench에서 S3, Gitea 내부 Service/Route, Nexus가 모두 HTTP `200`을 반환했다. 기존 EgressIP, `network-zone=s3`, `k8s.ovn.org/egress-assignable`은 남아 있지 않다.

**롤백**: host routing을 중단하려면 Network Operator 백업을 적용하거나 `routingViaHost=false`로 patch한다. 신규 Tuned와 `network.openshift.io/storage-route` label을 제거한 뒤, 특정 Namespace만 storage망으로 보내야 하면 별도 EgressIP 설계를 다시 적용한다.

```bash
oc patch network.operator.openshift.io cluster --type=merge \
  -p '{"spec":{"defaultNetwork":{"ovnKubernetesConfig":{"gatewayConfig":{"routingViaHost":false}}}}}'

oc delete tuned routing-via-host-storage-forwarding \
  -n openshift-cluster-node-tuning-operator --ignore-not-found
oc label node ocp-w01-gpu ocp-w02-cpu sno-node \
  network.openshift.io/storage-route-
```


### mc cli 설치
```bash
curl -L https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc
chmod +x /usr/local/bin/mc
```


## 기능별 작업 가이드

이 절은 위의 기본 DSC를 만든 뒤 원하는 기능을 추가할 때 사용한다. 기본 상태는 `kserve`, `workbenches`, `aipipelines`, `modelregistry`, `trustyai`, `trainer`가 `Managed`이고, GPU/Kueue/Ray/MaaS 계열은 `Removed`인 상태다.

### 먼저 구분할 것: 자원 Queue와 MaaS API quota

| 구분 | 구현 기능 | 제어 대상 |
|---|---|---|
| 워크로드 Queue | Red Hat build of Kueue | Workbench, Job, Trainer/Ray 같은 Kubernetes workload의 CPU·메모리·GPU admission |
| MaaS API quota | `MaaSSubscription` + Limitador | 사용자·그룹별 LLM API token 요청량과 사용 한도 |

MaaS 자체를 켜기 위해 Kueue가 필요한 것은 아니다. MaaS의 token quota를 Kueue `ClusterQueue`로 만들지 않는다. 반대로 Workbench와 학습 Job의 자원 대기·우선순위는 MaaSSubscription이 아니라 Kueue로 관리한다.

### 목적별 선택표

| 목적 | 필요한 구성 | DSC 변경 | 상세 실습 |
|---|---|---|---|
| 기본 Workbench를 YAML로 실행 | Workbenches, StorageClass/PVC | 이미 `workbenches: Managed` | [Week2 Day6](<Week2-Day6 실습.md>) |
| 대시보드에서 기본 Workbench 생성 | Kueue UI 비활성화, 기본 또는 Node형 HardwareProfile | `kueue: Removed` | 아래의 Kueue 미사용 모드 |
| 대시보드에서 Queue 기반 Workbench 생성 | Kueue Operator/operand, ClusterQueue, LocalQueue, Queue HardwareProfile | `kueue: Unmanaged` | [Week3 Day12](<Week3-Day12 실습.md>) |
| KFP v2 Data Science Pipeline | RHOAI AI Pipelines, S3 artifact storage | 이미 `aipipelines: Managed` | [Week2 Day7](<Week2-Day7 실습.md>) |
| Model Registry | Model Registry, PostgreSQL/MySQL | 이미 `modelregistry: Managed` | [Week2 Day8](<Week2-Day8 실습.md>) |
| KServe CPU RawDeployment | KServe, ServingRuntime, 모델 저장소 | 이미 `kserve: Managed` | Week1 Day3~5 |
| Trainer 기반 학습 Job | JobSet Operator와 `JobSetOperator/cluster` | 이미 `trainer: Managed` | Trainer 실습 |
| GPU Workbench/서빙/학습 | PCI passthrough, NFD, KMM, NVIDIA GPU Operator, ClusterPolicy, GPU HardwareProfile | KServe/Workbench는 기존 상태 사용 | [Week3 Day11](<Week3-Day11 실습.md>) |
| CPU/GPU quota·우선순위·공유 | Red Hat build of Kueue, Queue/Flavor/PriorityClass | `kueue: Unmanaged` | [Week3 Day12](<Week3-Day12 실습.md>) |
| Ray/CodeFlare 분산 workload | Ray component, Kueue | `ray: Managed`, `kueue: Unmanaged` | 분산 workload 보강 실습 |
| Monitoring/Guardrails | User Workload Monitoring, ServiceMonitor/Rule, TrustyAI 또는 NeMo | `trustyai`는 이미 `Managed` | [Week3 Day13](<Week3-Day13 실습.md>) |
| MaaS/LLM API key/token quota | GPU, LWS, RHCL/DNS/Authorino/Limitador, PostgreSQL, Gateway | `modelsAsService: Managed` | [Week3 Day14](<Week3-Day14 실습.md>) |
| Tekton CI/CD | OpenShift Pipelines Operator | DSC 변경 없음 | [Week2 Day10](<Week2-Day10 실습.md>) |
| Argo CD GitOps | OpenShift GitOps Operator | DSC 변경 없음 | [Week2 Day10](<Week2-Day10 실습.md>) |
| 백업/복구 | OADP Operator와 백업 저장소 | DSC 변경 없음 | 백업/DR 보강 실습 |

### 대시보드 Workbench의 Kueue 사용 여부

공식 문서: [Managing workloads with Kueue](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/managing_openshift_ai/managing-workloads-with-kueue)

대시보드로 Workbench를 만든다는 이유만으로 Kueue가 필수인 것은 아니다. Dashboard 설정과 HardwareProfile의 workload allocation strategy에 따라 다음 두 모드 중 하나를 사용한다.

| 모드 | Dashboard `disableKueue` | DSC `kueue` | HardwareProfile scheduling | Namespace |
|---|---:|---|---|---|
| Kueue 미사용 | `true` | `Removed` | 기본값 또는 `Node` | Kueue managed label 없음 |
| Kueue 사용 | `false` | `Unmanaged` | `Queue` + LocalQueue | `kueue.openshift.io/managed=true` |

현재처럼 DSC가 `Removed`인데 `disableKueue`가 없거나 `false`이면 Dashboard는 Kueue UI를 활성화한 상태에서 backend를 찾지 못해 Workbench 생성 화면을 막을 수 있다. Kueue를 사용하지 않을 때는 두 설정을 명시적으로 맞춘다.

```bash
# 대시보드 기본 Workbench: Kueue를 사용하지 않는 모드
oc patch odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications --type=merge \
  -p '{"spec":{"dashboardConfig":{"disableKueue":true}}}'

oc patch dsc default-dsc --type=merge \
  -p '{"spec":{"components":{"kueue":{"managementState":"Removed","defaultClusterQueueName":"default","defaultLocalQueueName":"default"}}}}'

oc label namespace jukebox kueue.openshift.io/managed-
```

이 모드에서는 `default-profile`처럼 Queue 설정이 없는 HardwareProfile을 선택한다. 특정 노드로 직접 배치하려면 `spec.scheduling.type: Node`와 `nodeSelector`/`tolerations`를 가진 HardwareProfile을 사용한다.

### Queue 기반 Workbench 구성

공식 문서: [Installing distributed workloads components](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/installing_and_uninstalling_openshift_ai_self-managed_in_a_disconnected_environment/installing-the-distributed-workloads-components_install), [Working with hardware profiles](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/working_with_accelerators/index#working-with-hardware-profiles_accelerators)

**목적**: 대시보드에서 생성한 Workbench를 `team-lq`로 admission하고, CPU·메모리·GPU quota와 우선순위를 적용한다.

**방법**:

1. `kueue-operator` Subscription을 설치한다.
2. Operator CSV 예제에 맞춰 `Kueue/cluster` operand를 생성한다.
3. `ResourceFlavor`, `ClusterQueue/team-cq`, `LocalQueue/team-lq`, `WorkloadPriorityClass/day12-low`를 생성한다.
4. 대상 Namespace를 Kueue 관리 대상으로 지정한다.
5. DSC는 외부 Kueue를 사용하도록 `Unmanaged`로 전환한다.
6. Dashboard의 Kueue UI를 활성화한다.
7. `team-lq`를 사용하는 Queue형 HardwareProfile을 만든다.

```bash
oc label namespace jukebox kueue.openshift.io/managed=true --overwrite

oc patch dsc default-dsc --type=merge \
  -p '{"spec":{"components":{"kueue":{"managementState":"Unmanaged","defaultClusterQueueName":"team-cq","defaultLocalQueueName":"team-lq"}}}}'

oc patch odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications --type=merge \
  -p '{"spec":{"dashboardConfig":{"disableKueue":false}}}'
```

Queue형 HardwareProfile의 핵심 필드는 다음과 같다. `LocalQueue/team-lq`는 Workbench가 생성되는 각 프로젝트 Namespace에 있어야 한다.

```yaml
apiVersion: infrastructure.opendatahub.io/v1
kind: HardwareProfile
metadata:
  name: queued-cpu
  namespace: redhat-ods-applications
  annotations:
    opendatahub.io/display-name: Queue CPU
    opendatahub.io/disabled: "false"
  labels:
    app.kubernetes.io/part-of: hardwareprofile
    app.opendatahub.io/hardwareprofile: "true"
spec:
  identifiers:
    - identifier: cpu
      displayName: CPU
      resourceType: CPU
      minCount: 1
      defaultCount: 2
      maxCount: 4
    - identifier: memory
      displayName: Memory
      resourceType: Memory
      minCount: 2Gi
      defaultCount: 4Gi
      maxCount: 8Gi
  scheduling:
    type: Queue
    kueue:
      localQueueName: team-lq
      priorityClass: day12-low
```

```bash
oc get kueue -A
oc get clusterqueue team-cq
oc get localqueue team-lq -n jukebox
oc get hardwareprofile queued-cpu -n redhat-ods-applications -o yaml
oc get workload -n jukebox
```

YAML로 `Notebook`을 직접 생성하는 기본 Day6 경로와 대시보드의 Kueue 미사용 모드는 모두 Kueue 없이 실행할 수 있다. Queue형 HardwareProfile을 선택하는 경우에만 Kueue와 LocalQueue가 필요하다.

공식 절차는 [Working with hardware profiles](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/working_with_accelerators/index#working-with-hardware-profiles_accelerators)를 참고한다. HardwareProfile 생성 화면의 `Local queue` 선택지는 클러스터가 Kueue workload management를 사용하도록 구성된 경우에만 제공된다.

### GPU Workbench·서빙·학습 구성

공식 문서: [Enabling accelerators](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/installing_and_uninstalling_openshift_ai_self-managed_in_a_disconnected_environment/enabling-accelerators_install), [Provision hardware configurations and resources](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/working_with_accelerators/index)

**목적**: VM/노드에 연결된 NVIDIA GPU를 `nvidia.com/gpu` 리소스로 노출하고 RHOAI에서 선택한다.

**방법**:

1. guest `lspci`에서 NVIDIA PCI 장치를 먼저 확인한다.
2. NFD Operator와 `NodeFeatureDiscovery`를 설치한다.
3. KMM Operator를 설치한다.
4. NVIDIA GPU Operator와 `ClusterPolicy`를 설치한다.
5. GPU capacity와 `nvidia-smi`를 확인한다.
6. `nvidia.com/gpu` identifier를 가진 HardwareProfile을 생성한다.
7. GPU 공유·quota가 필요하면 그 다음 Kueue와 GPU ResourceFlavor를 구성한다.

```bash
oc debug node/ocp-w01-gpu -- chroot /host \
  lspci -nn | grep -i nvidia

oc get clusterpolicy
oc get node ocp-w01-gpu \
  -o jsonpath='{.status.allocatable.nvidia\.com/gpu}{"\n"}'
oc get pods -n nvidia-gpu-operator
```

PCI 장치가 보이지 않는 상태에서는 Operator 설치를 진행하지 않는다. 자세한 설치 YAML과 mirror 진단은 [Week3 Day11](<Week3-Day11 실습.md>)을 따른다.

### KServe RawDeployment 구성

공식 문서: [Deploy models with KServe RawDeployment](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/deploying_models/index)

**목적**: CPU 또는 단일 GPU 모델을 KServe `InferenceService`로 서빙한다.

**방법**:

1. `kserve: Managed`와 `KserveReady=True`를 확인한다.
2. 모델 형식에 맞는 `ServingRuntime`을 선택하거나 생성한다.
3. S3/PVC/OCI ModelCar 연결을 준비한다.
4. `InferenceService`를 생성하고 Predictor Pod와 endpoint를 확인한다.

```bash
oc get dsc default-dsc \
  -o jsonpath='{.spec.components.kserve.managementState}{"\n"}'
oc get servingruntime -A
oc get inferenceservice -A
```

기본 RawDeployment에는 RHCL, LWS, Kueue가 직접 필요하지 않다. GPU 모델인 경우에만 GPU Operator와 GPU HardwareProfile이 추가로 필요하다.

`rawDeploymentServiceConfig: Headless`이면 predictor Service는 `clusterIP: None`이다. 같은 클러스터의 Pod에서 Service DNS를 직접 호출할 때는 Service의 `port: 80`이 아니라 predictor가 실제로 수신하는 `8080`을 사용한다. 예: `http://<isvc>-predictor.<namespace>.svc.cluster.local:8080`.

### AI Pipelines와 Model Registry 구성

공식 문서: [Get started with projects, workbenches, and pipelines](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/getting_started_with_red_hat_openshift_ai_self-managed/index), [Managing and monitoring models](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/managing_and_monitoring_models/index)

**목적**: KFP v2 pipeline을 실행하고 생성된 모델 버전을 Registry에 기록한다.

**방법**:

1. `aipipelines: Managed`, `modelregistry: Managed`를 확인한다.
2. Pipeline artifact 저장용 S3 connection을 만든다.
3. DataSciencePipelinesApplication을 생성한다.
4. Registry용 PostgreSQL/MySQL과 ModelRegistry CR을 준비한다.
5. Pipeline에서 모델을 저장하고 Registry version/artifact를 등록한다.

```bash
oc get dsc default-dsc -o json | jq \
  '.spec.components | {aipipelines, modelregistry}'
oc get datasciencepipelinesapplication -A
oc get modelregistries.modelregistry.opendatahub.io -A
```

RHOAI AI Pipelines의 실행 엔진은 bundled Argo Workflows다. OpenShift Pipelines(Tekton)과 OpenShift GitOps(Argo CD)는 이 기능의 필수 의존성이 아니다.

### Trainer와 Ray/CodeFlare 구성

공식 문서: [Accelerate data processing and training with distributed workloads](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/working_with_distributed_workloads/index), [Installing distributed workloads components](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/installing_and_uninstalling_openshift_ai_self-managed_in_a_disconnected_environment/installing-the-distributed-workloads-components_install)

**목적**: 단일 Pod를 넘는 학습·분산 workload를 JobSet과 Ray로 실행하고 Kueue admission을 적용한다.

**방법**:

- Trainer: `job-set` Subscription뿐 아니라 `JobSetOperator/cluster` operand와 controller Pod까지 확인한다. DSC `trainer`는 이미 `Managed`다.
- Ray/CodeFlare: Kueue를 먼저 구성하고 DSC `ray`를 `Managed`로 전환한다.

```bash
oc get jobsetoperator cluster
oc get pods -n openshift-jobset-operator

oc patch dsc default-dsc --type=merge \
  -p '{"spec":{"components":{"ray":{"managementState":"Managed"}}}}'

oc get dsc default-dsc \
  -o jsonpath='{.status.conditions[?(@.type=="RayReady")]}{"\n"}'
```

Trainer는 controller 상태만 보지 말고 실제 `TrainJob`이 `JobSet`을 만들고 완료되는지 확인한다. Kueue를 사용하는 예시는 다음과 같다.

```yaml
apiVersion: trainer.kubeflow.org/v1alpha1
kind: TrainJob
metadata:
  name: trainer-smoke
  namespace: jukebox
  labels:
    kueue.x-k8s.io/queue-name: team-lq
spec:
  runtimeRef:
    name: torch-distributed-cpu-torch210-py312
  suspend: true
  trainer:
    numNodes: 1
    command: [python]
    args: ["-c", "import torch; print('trainer-ok', torch.__version__)"]
    resourcesPerNode:
      requests: {cpu: "1", memory: 2Gi}
      limits: {cpu: "2", memory: 4Gi}
```

```bash
oc get trainjob,jobset,job,pod,workload -n jukebox
oc logs -n jukebox -l jobset.sigs.k8s.io/jobset-name=trainer-smoke --all-containers
```

2026-07-12 검증에서는 Kueue가 `TrainJob`을 admit한 뒤 JobSet/Job/Pod를 생성했고 `Complete=True`, `trainer-ok 2.10.0`을 확인했다. Ray는 RHOAI 3.4 workbench 이미지의 Ray 2.53.0으로 head 3Gi/worker 2Gi request를 사용했을 때 `SUCCEEDED`와 `ray-ok [0, 1, 4, 9]`를 확인했다. 2Gi head limit는 초기화 중 OOM이 발생했다.

분산 실습을 끝내고 기본 상태로 돌아갈 때는 실행 중인 Ray workload를 먼저 제거한 뒤 `ray: Removed`로 되돌린다.

### Monitoring과 Guardrails 구성

공식 문서: [Monitoring your AI systems](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/monitoring_your_ai_systems/index), [Enabling AI safety with NeMo Guardrails](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/enabling_ai_safety_with_guardrails/enabling-ai-safety-with-guardrails_safety)

**목적**: 사용자 workload metric, 추론 latency/error, GPU metric과 Guardrails 차단 결과를 관측한다.

**방법**:

1. User Workload Monitoring을 활성화한다.
2. 대상 Service에 맞는 ServiceMonitor와 PrometheusRule을 만든다.
3. GPU metric은 NVIDIA GPU Operator의 DCGM exporter 설치 후 확인한다.
4. TrustyAI 또는 NeMo Guardrails를 배포하고 정상/차단 요청을 모두 검증한다.

```bash
oc get configmap cluster-monitoring-config -n openshift-monitoring -o yaml
oc get pods -n openshift-user-workload-monitoring
oc get servicemonitor,prometheusrule -A
```

자세한 설정과 정리 절차는 [Week3 Day13](<Week3-Day13 실습.md>)을 따른다.

### MaaS와 LLM API quota 구성

공식 문서: [Govern LLM access with Models-as-a-Service](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/govern_llm_access_with_models-as-a-service/index)

**목적**: LLM을 공통 endpoint로 publish하고 사용자·그룹별 API key, authorization, token quota를 적용한다.

**필수 구성**:

- GPU와 NVIDIA GPU Operator
- Leader Worker Set Operator
- RHCL 1.4.1과 dependent DNS 1.4.0, Authorino 1.4.1, Limitador 1.4.0
- MaaS용 PostgreSQL 14 이상
- Gateway/Route와 OpenShift service CA 신뢰
- 내부 OCI ModelCar 또는 지원되는 모델 URI

**방법**:

1. RHCL dependent CSV와 LWS controller를 확인한다.
2. MaaS PostgreSQL과 DB connection Secret을 준비한다.
3. MaaS Gateway/Route를 만든다.
4. DSC의 `modelsAsService`를 `Managed`로 전환한다.
5. Dashboard의 MaaS와 MaaS authorization policy 기능을 활성화한다.
6. LLMInferenceService를 배포하고 MaaSModelRef로 publish한다.
7. MaaSSubscription과 MaaSAuthPolicy를 생성한다.
8. OpenShift token으로 관리 API, MaaS API key로 model endpoint를 검증한다.

```bash
oc patch dsc default-dsc --type=merge \
  -p '{"spec":{"components":{"kserve":{"modelsAsService":{"managementState":"Managed"}}}}}'

oc patch odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications --type=merge \
  -p '{"spec":{"dashboardConfig":{"modelAsService":true,"maasAuthPolicies":true}}}'

oc get pods -n redhat-ods-applications | grep maas
oc get llminferenceservice -A
oc get maasmodelref -A
oc get maassubscription,maasauthpolicy -n models-as-a-service
```

Kueue는 MaaS control plane의 직접 의존성이 아니다. LLM API 사용량 제한은 `MaaSSubscription`과 Limitador로 구성한다. 전체 절차는 [Week3 Day14](<Week3-Day14 실습.md>)을 따른다.

### Tekton CI/CD와 Argo CD GitOps 구성

공식 문서: [Installing OpenShift Pipelines](https://docs.redhat.com/en/documentation/red_hat_openshift_pipelines/1.22/html/installing_and_configuring), [Installing OpenShift GitOps](https://docs.redhat.com/en/documentation/red_hat_openshift_gitops/1.21/html/installing_gitops/installing-openshift-gitops)

**목적**: 모델 build/test/deploy를 CI pipeline과 GitOps reconciliation으로 자동화한다.

**방법**:

1. Tekton Task/Pipeline/PipelineRun이 필요할 때 OpenShift Pipelines Operator를 설치한다.
2. manifest repository를 지속 동기화할 때 OpenShift GitOps Operator를 설치한다.
3. 두 Operator는 RHOAI `aipipelines`와 별개로 설치하고 DSC를 변경하지 않는다.

```bash
oc get subscription -A | grep -E \
  'openshift-pipelines-operator-rh|openshift-gitops-operator'
oc get tektonconfig
oc get argocd -A
```

Operator 준비 상태만 확인하지 말고 최소 PipelineRun을 실행한다.

```yaml
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: pipeline-smoke-
  namespace: jukebox
spec:
  pipelineSpec:
    tasks:
      - name: validate
        taskSpec:
          steps:
            - name: run
              image: registry.redhat.io/rhoai/odh-pipeline-runtime-datascience-cpu-py312-rhel9@sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661
              command: [python]
              args: ["-c", "print('tekton-ok')"]
```

`generateName`을 사용하므로 위 YAML은 `oc apply`가 아니라 `oc create -f`로 생성한다. 2026-07-12 검증에서는 PipelineRun `Succeeded=True`와 `tekton-ok`를 확인했고, Argo CD는 내부 Gitea의 ConfigMap을 `Synced/Healthy`로 동기화한 뒤 수동 변경을 Git 선언으로 self-heal했다.

Argo CD GitOps 기능 실습은 [Week2 Day10](<Week2-Day10 실습.md>)을 따른다. Tekton은 Day10과 Day11~15 기본 과정에서 사용하지 않으며, 모델 build/test와 manifest 갱신까지 CI로 자동화하는 별도 확장에서 사용한다.

### OADP 백업·복구 구성

공식 문서: [OADP application backup and restore](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/backup_and_restore/oadp-application-backup-and-restore)

**목적**: RHOAI 프로젝트의 Kubernetes 리소스와 PVC를 S3 호환 저장소에 백업한다. DB 기반 컴포넌트는 OADP 파일 백업만으로 애플리케이션 일관성이 보장되지 않으므로 PostgreSQL/MySQL dump 또는 정지 절차를 별도로 설계한다.

**방법**:

1. `redhat-oadp-operator`를 현재 미러 카탈로그의 `stable` 채널로 설치한다.
2. S3 자격증명 Secret과 `DataProtectionApplication`을 만든다.
3. 위의 `routingViaHost`와 storage NIC forwarding 구성을 먼저 완료한다. cluster-wide host routing을 사용하므로 `openshift-adp` Namespace에 EgressIP selector label을 추가하지 않는다.
4. `BackupStorageLocation`이 `Available`인지 확인한 후 `Backup`을 생성한다.

```bash
oc get csv -n openshift-adp
oc get dataprotectionapplication,backupstoragelocation -n openshift-adp
oc get backup -n openshift-adp
```

2026-07-12 EgressIP 구성에서 OADP 1.6.0, MinIO S3, `snapshotVolumes: false` 조합으로 테스트 Namespace의 63개 리소스가 오류와 경고 없이 `Completed`가 됐다. 2026-07-14 `routingViaHost` 전환 후 Workbench의 S3 기본 연결은 재검증했으며, OADP Backup/Restore 전체 재검증은 해당 실습에서 수행한다.

### 선택 컴포넌트 전환 원칙

공식 문서: [Creating distributed data processing applications with the Kubeflow Spark Operator](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/creating_distributed_data_processing_applications_with_the_kubeflow_spark_operator/overview-of-kubeflow-operator_data-processing), [Deliver consistent ML features with Feature Store](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/working_with_machine_learning_features/index), [Build AI applications with Llama Stack](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/working_with_llama_stack/index), [Distributed workloads](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/working_with_distributed_workloads/index)

| 컴포넌트 | 켜는 시점 | 함께 확인할 외부 의존성 |
|---|---|---|
| `sparkoperator` | Spark 기반 대규모 데이터 처리 | Spark application image, object storage |
| `feastoperator` | Online/Offline Feature Store | DB, object storage, Feast registry |
| `llamastackoperator` | Llama Stack 기반 RAG/Agent API | vector DB, model endpoint, provider image |
| `trainingoperator` | 별도 Kubeflow Training Operator API가 필요한 경우 | JobSet/Kueue/GPU 조합 검토 |

사용 이유와 외부 의존성을 먼저 확정하고 한 컴포넌트씩 `Managed`로 전환한다. 여러 컴포넌트를 동시에 켜면 폐쇄망 image 누락과 dependency 오류의 원인을 분리하기 어렵다.
