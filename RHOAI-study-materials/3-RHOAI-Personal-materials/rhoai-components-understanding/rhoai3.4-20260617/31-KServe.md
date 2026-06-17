# KServe (단일 모델 서빙)

> 모델별로 전용 서버를 띄우는 single-model serving 플랫폼. RHOAI의 기본 서빙 컴포넌트.
> 영역: [30-모델서빙-관계](30-모델서빙-관계.md)

---

## 1. 정의 / 역할
- 모델 1개당 1개 서버(Pod). LLM 등 리소스 큰 모델의 배포/모니터링/스케일/유지보수 담당.
- 모델 타입·포맷·하드웨어 프로파일을 분석해 최적 ServingRuntime 자동 선택 가능.

## 2. 버전 / 라이프사이클
- 업스트림: **`kserve/kserve`**, RHOAI 3.4 = **0.17.0 GA**.
- v0.17.0: Helm 차트 재구조화(breaking), LLMInferenceService autoscaling/WVA, Gateway API v1.4.0, GIE v1.2.0, knative-serving v1.21.1 번들(Serverless 코드 자체는 잔존).

## 3. 아키텍처
- **컨트롤 플레인(상주)**: KServe 컨트롤러가 InferenceService를 watch → 하위 K8s 리소스 reconcile.
- **데이터 플레인(요청별)**: 실제 추론 트래픽을 처리하는 모델 서버 Pod.

## 4. CRD

| CRD | group/version | scope | 역할 |
|---|---|---|---|
| **InferenceService** | `serving.kserve.io/v1beta1` | Namespaced | 배포된 모델 인스턴스 |
| **ServingRuntime** | `serving.kserve.io/v1alpha1` | Namespaced | 서빙 Pod 템플릿(프로젝트) |
| **ClusterServingRuntime** | `serving.kserve.io/v1alpha1` | Cluster | 서빙 Pod 템플릿(전역) |

### InferenceService 핵심 spec
- `predictor`(필수) / `transformer` / `explainer`.
- `predictor.model`: `modelFormat{name, version}`(onnx/pytorch/huggingface), `runtime`(런타임 명시), `storageUri`(s3://, pvc://, oci://, hf://), `resources`.

### ServingRuntime 핵심 spec
- `supportedModelFormats[]{name, version, autoSelect, priority}`, `containers[]`(image/args/resources), `multiModel`, `protocolVersions`.
- ServingRuntime vs ClusterServingRuntime = **scope만 차이**(spec 동일).

### 런타임 선택 로직
1. **명시**: `predictor.model.runtime: <이름>` → 강제.
2. **자동**: 생략 시 `modelFormat`을 모든 런타임의 `supportedModelFormats`와 대조, **`autoSelect: true`**만 후보.
3. **타이브레이크**: 다수 매치 시 **`priority` 큰** 런타임. (같은 키에 동일 priority 금지 → 비결정적)

## 5. 동작 방식 (★배포 모드)
배포 모드 = 어노테이션 `serving.kserve.io/deploymentMode` 우선, 없으면 ConfigMap 기본값. **RHOAI 3.4 기본 = RawDeployment**.

- **RawDeployment** (UI "Standard") → 컨트롤러가 생성:
  - **Deployment**(모델 서버 Pod) + **Service**
  - 오토스케일: 기본 **HPA**(CPU/메모리) 또는 **KEDA ScaledObject**(`serving.kserve.io/autoscalerClass: keda`, 메트릭 Resource/External(Prometheus)/PodMetrics). **KEDA는 RawDeployment 전용 + 3.4 TP**.
- **Serverless** → **Knative Service 1개**(Knative Serving + Istio 필요, scale-to-zero). **2.25 deprecated** → RawDeployment 마이그레이션(3.3 업그레이드 전 2.25에서 선행).

## 6. vLLM ServingRuntime
- 변형: vLLM NVIDIA GPU / CPU(Z·Power) / Gaudi / AMD / Spyre.
- OpenAI 호환: `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings` (HTTPS :443). v0.17.0 번들 vLLM = 0.15.1.

## 7. 인증 / 연동
- "Require token authentication" → `Authorization: Bearer <token>`.
- Model Registry에서 배포(`storageUri` 직접 또는 `model-registry://` CSI resolve) → [51-Model-Registry](51-Model-Registry.md).
- 분산이 필요하면 llm-d로 → [32-llm-d-분산추론](32-llm-d-분산추론.md).

## 8. 운영 함정
- Serverless deprecated → 3.3+ 전 2.25에서 RawDeployment 마이그레이션.
- 자동 런타임 선택: 동일 accelerator에 템플릿 여러 개면 비활성될 수 있어 명시 `runtime:` 권장.
- KEDA는 RawDeployment 전용 + 3.4 TP.
- 같은 modelFormat에 priority 동률 금지.

## 9. 출처
- 소스: https://github.com/kserve/kserve , v0.17.0 릴리스
- ServingRuntime 개념: https://kserve.github.io/website/docs/concepts/resources/servingruntime
- 마이그레이션(Serverless→Raw): https://access.redhat.com/articles/7134025
