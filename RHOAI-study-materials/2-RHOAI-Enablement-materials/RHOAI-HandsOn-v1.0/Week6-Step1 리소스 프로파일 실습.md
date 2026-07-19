# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 6 - Step 1 리소스 확보와 OCI 연결

> 사전 활성화: [Week6 Step 0](<Week6-Step0 사전점검 실습.md>)에서 GPU capacity/allocatable `2/2`와 inventory Job 성공을 확인한다.

TP2 Pod를 배치할 수 있는 CPU·메모리 request 여유를 확인하고, 필요할 때만 RHOAI Dashboard operand를 잠시 제거한다. KServe controller와 GPU Operator 계열은 이 실습의 필수 구성이라 중지하지 않는다.

### 현재 request 재확인

```bash
oc describe node ocp-w01-gpu | \
  sed -n '/Allocated resources:/,/Events:/p'

oc get pods -A --field-selector spec.nodeName=ocp-w01-gpu \
  -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase
```

다음 두 조건이면 Dashboard를 유지해도 TP2 request가 admission된다.

- 기존 memory request + `8Gi`가 allocatable memory보다 작다.
- 기존 CPU request + `4`가 allocatable CPU보다 작다.

2026-07-16 기준으로 두 조건을 만족한다. 이후 workload가 늘어 여유가 부족하거나 TP 실행 중 host memory 압박을 줄이려면 다음 선택 절차를 사용한다.

### 선택: Dashboard operand 임시 제거

Dashboard는 CLI 기반 TP 검증에 필요하지 않고 현재 GPU worker의 replica 한 개가 약 `3.1 CPU / 5.5Gi`를 요청한다. 전체 DSC가 아니라 Dashboard component만 정확히 백업하고 제거한다.

```bash
oc get dsc default-dsc -o json | \
  jq '.spec.components.dashboard' \
  > /tmp/week6-dashboard-before.json

cat /tmp/week6-dashboard-before.json

oc patch dsc default-dsc --type=merge \
  -p '{"spec":{"components":{"dashboard":{"managementState":"Removed"}}}}'

oc wait --for=condition=Ready dsc/default-dsc --timeout=600s
oc get pods -n redhat-ods-applications | grep rhods-dashboard || true
```

`modelsAsService`, Model Registry, AI Pipelines, Workbenches, MLflow, Trainer와 TrustyAI도 TP 자체에는 필요하지 않지만 이번 기능 검증에서는 제거하지 않는다. 대부분 GPU worker에서 큰 request를 차지하지 않고, 상태 저장 component와 여러 controller를 함께 재구성하는 비용이 절감량보다 크기 때문이다. 외부 Operator Subscription을 uninstall하거나 CSV를 삭제하지 않는다.

### 유지해야 하는 구성

| 구성 | 유지 이유 |
|---|---|
| RHOAI Operator와 KServe | ServingRuntime/InferenceService reconcile |
| NFD, KMM, NVIDIA GPU Operator | 드라이버와 `nvidia.com/gpu` 공급 |
| Device Plugin, GFD, DCGM Exporter | GPU 할당·label·관측 |
| cert-manager | KServe controller 의존성 |
| OpenShift DNS/OVN/registry/monitoring | Pod 통신과 플랫폼 기본 기능 |

Ray, Kueue, JobSet, LeaderWorkerSet, OpenShift Pipelines와 GitOps는 **이 단일 Pod TP 경로에서 사용하지 않는다**. 이미 설치돼 있어도 GPU worker의 핵심 여유를 크게 줄이지 않으므로 실습을 위해 uninstall하지 않는다.

### OCI ModelCar pull Secret

Day14에서 반입한 Qwen2.5 0.5B ModelCar를 재사용한다. 공개 문서나 shell 파일에 실제 ID/PW를 기록하지 않는다.

```bash
read -rp 'Model registry ID: ' MODEL_REGISTRY_ID
read -rsp 'Model registry password: ' MODEL_REGISTRY_PW
echo

oc create secret docker-registry week6-model-registry \
  -n rhoai-tp-lab \
  --docker-server=192.168.10.50:5010 \
  --docker-username="$MODEL_REGISTRY_ID" \
  --docker-password="$MODEL_REGISTRY_PW" \
  --dry-run=client -o yaml | oc apply -f -

unset MODEL_REGISTRY_ID MODEL_REGISTRY_PW

oc get secret week6-model-registry -n rhoai-tp-lab \
  -o jsonpath='{.type}{"\n"}'
```

Secret type은 `kubernetes.io/dockerconfigjson`이어야 한다. 모델 URI는 다음 두 단계에서 immutable tag를 사용한다.

```text
oci://192.168.10.50:5010/models/qwen2.5-0.5b-instruct:7ae5576
```

### 확인 기준

- GPU worker에 TP2 Pod request를 더한 뒤에도 CPU와 memory request 여유가 있다.
- 선택 절차를 수행했다면 `/tmp/week6-dashboard-before.json`이 존재하고 Dashboard Pod가 제거됐다.
- `rhoai-tp-lab/week6-model-registry` Secret이 존재한다.
- KServe와 NVIDIA GPU Operator 관련 controller/DaemonSet은 정상이다.
