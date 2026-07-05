# 오퍼레이터 설치

## 오퍼레이터 준비/미러링 (홈서버 기준 RHOAI 기능테스트에 필요할 것 같은 모든 오퍼레이터를 준비한거라 실제로는 필요하지 않거나, 누락된 게 있을 수 있음)

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
      - name: rhcl-operator
        channels:
          - name: stable
      - name: authorino-operator
        channels:
          - name: stable
      - name: limitador-operator
        channels:
          - name: stable

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

### 당초 검토했다가 제외한 미러 대상

아래 항목은 "있으면 좋다"가 아니라 현재 홈랩에서 실제 검증 가능한지 기준으로 제외했다. 나중에 하드웨어나 테스트 목표가 바뀌면 다시 포함한다.
| Package | 제외 이유 |
|---|---|
| `odf-operator` | 단일 홈서버 환경에서 리소스 부담이 크고, 현재 PVC/S3는 TrueNAS NFS CSI/S3로 대체한다. |
| `sriov-network-operator` | SR-IOV capable NIC/VF 설계가 현재 홈랩에 없다. |
| `nvidia-network-operator` | Mellanox/ConnectX, RDMA/RoCE, GPUDirect RDMA 환경이 아니다. |
| `ibm-spyre-operator` | IBM Spyre 가속기 하드웨어가 없다. |
| `kuadrant-operator` | community catalog 쪽 deprecated 가능성이 있어 RHCL + Authorino + Limitador 경로를 우선한다. |
| `openshift-serverless-operator` | RHOAI 3.4 기본 서빙은 KServe RawDeployment 기준이고, KServe Serverless deployment mode는 deprecated다. |
| `metallb-operator` | 현재 홈랩은 Bastion HAProxy/DNS와 VM 내부망으로 충분하다. 별도 LoadBalancer 실습 때만 포함한다. |
| `dns-operator` | OCP 기본 DNS와 Bastion DNS 구성이 현재 목적에 충분하다. 외부 DNS 자동화 실습 때만 포함한다. |



## 오퍼레이터 설치 순서

### Red Hat OpenShift AI 오퍼레이터 설치
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

### node tuning operator(기본 오퍼레이터) 이용해서 ip forwarding 설정 노드튜닝 하기
```bash
oc apply -f <<'EOF'
apiVersion: tuned.openshift.io/v1
kind: Tuned
metadata:
  name: s3-egressip-forwarding
  namespace: openshift-cluster-node-tuning-operator
spec:
  profile:
    - name: s3-egressip-forwarding
      data: |
        [main]
        summary=Enable IPv4 forwarding on the storage NIC for S3 EgressIP
        include=openshift-node

        [sysctl]
        net.ipv4.conf.enp6s19.forwarding=1
  recommend:
    - match:
        - label: k8s.ovn.org/egress-assignable
          value: !!str true
      priority: 20
      profile: s3-egressip-forwarding
EOF

oc label node ocp-w01-gpu k8s.ovn.org/egress-assignable=true --overwrite
oc label node ocp-w02-cpu k8s.ovn.org/egress-assignable=true --overwrite

oc label ns jukebox network-zone=s3 --overwrite

oc apply -f <<'EOF'
apiVersion: k8s.ovn.org/v1
kind: EgressIP
metadata:
  name: s3-storage-egress
spec:
  egressIPs:
    - 192.168.20.55
  namespaceSelector:
    matchLabels:
      network-zone: s3
EOF

## 검증
oc get egressip s3-storage-egress -oyaml
oc get ns jukebox --show-labels
oc get nodes -l k8s.ovn.org/egress-assignable --show-labels
```


### mc cli 설치
```bash
curl -L https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc
chmod +x /usr/local/bin/mc
```


**이 아래쪽은 미리 정리만 했을 뿐 아직 검증되지 않았습니다.**

### GPU 사용을 위해 필요한 오퍼레이터 설치
1. NFD 오퍼레이터 설치 > NodeFeatureDiscovery 인스턴스 생성
2. kernel-module-management 오퍼레이터 설치 (필수는 아님)
3. NVIDIA GPU 오퍼레이터 설치 > ClusterPolicy 인스턴스 생성
4. RHOAI의 HardwareProfile 인스턴스 생성

### CICD를 별도 파이프라인으로 관리를 위한 오퍼레이터 설치
1. Red Hat Pipelines 오퍼레이터 설치
2. Red Hat GitOps 오퍼레이터 설치

