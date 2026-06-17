# llm-d 분산추론 (Distributed Inference with llm-d)

> Kubernetes 네이티브 **분산/분리(disaggregated) LLM 추론** 프레임워크 = vLLM(엔진) + Gateway API Inference Extension(지능형 라우팅). 3.4에서 GA.
> 영역: [30-모델서빙-관계](30-모델서빙-관계.md)

---

## 1. 정의 / 역할
단일 KServe가 감당 못 하는 **대규모/고처리량 LLM**을 **Prefill/Decode 분리, KV-cache aware 라우팅, 멀티노드 병렬**로 서빙.

## 2. 버전 / 라이프사이클
- 업스트림: **`llm-d/llm-d`**, RHOAI 3.4 = **0.7.1**. **3.4 GA**(3.0~3.3 TP). OCP **4.20+ 필수**. CNCF Sandbox.
- 제품 라인 주의: 동명 llm-d가 별도 제품 "Red Hat AI Inference"에선 TP(0.6). 본 노트는 **RHOAI 3.4(0.7.1, GA)** 기준.

## 3. CRD

| CRD | group/version | scope | 역할 |
|---|---|---|---|
| **LLMInferenceService** | `serving.kserve.io` (served v1alpha1, storage v1alpha2) | Namespaced | 분산 LLM 서빙 인스턴스 (`llmisvc`) |
| **LLMInferenceServiceConfig** | 동일 | Namespaced | 부분 spec 프리셋 템플릿 |

### LLMInferenceService 핵심 spec
- `model{uri(필수), name, criticality, lora}`.
- `template`/`worker`/`replicas`/`scaling`/`parallelism`(tensor/pipeline/data/expert).
- `router{route(HTTPRoute)/gateway/scheduler(EPP+InferencePool)}`.
- `prefill: WorkloadSpec`(P/D 분리 시), `baseRefs[]`(Config 합성).
- **토폴로지 자동 판별**: `worker` 있으면 멀티노드(LeaderWorkerSet), `prefill` 있으면 P/D 분리, 둘 다 없으면 단일노드 decode.
- **3.4 신규 `endpointPickerConfig`**: 스케줄러 설정을 인라인/ConfigMap으로(이전의 장황한 `--configText` 인자 대체).

### LLMInferenceServiceConfig
- 동일 스키마의 **부분 spec 템플릿**. **`baseRefs`로 M:1 합성**(StrategicMergePatch). RHOAI 문서상 custom ServingRuntime 정의를 대체(vLLM 인자는 컨테이너 `args`).
- Well-Known 프리셋: `kserve-config-llm-template`(단일노드), `…-worker-data-parallel`, `…-decode-template`, `…-prefill-template`, `…-router-route`, `…-scheduler`.

> 유추 주의: ServingRuntime→ISVC는 1:N 참조, **Config→LLMISVC는 M:1 합성**(방향 반대).

## 4. 동작 — 생성 리소스
LLMInferenceService 하나가 만드는 것:
- **워크로드**: Deployment(decode/단일노드) / LeaderWorkerSet(멀티노드) / Deployment(prefill 전용).
- **네트워킹**: Service(:8000) + **InferencePool**(`inference.networking.k8s.io/v1`) + **HTTPRoute**(`/v1/completions|chat/completions` + URLRewrite) + Gateway.
- **스케줄러/EPP**: EPP Deployment(`/app/epp` :9002 ext-proc) + EPP Service.

**요청 경로**: `Gateway(Envoy) → HTTPRoute → InferencePool → EPP(KV-cache aware 엔드포인트 선택) → 워크로드 Pod :8000`

## 5. Gateway API Inference Extension (GIE)
- **InferencePool**: 동일 모델 서버 Pod 집합을 selector로 묶고 EPP 참조. HTTPRoute의 backendRef.
  - api group이 졸업으로 변경: alpha `inference.networking.x-k8s.io/v1alpha2` → **GA `inference.networking.k8s.io/v1`** (YAML 호환 주의).
- **InferenceObjective**(`x-k8s.io/v1alpha2`, Alpha): 구 InferenceModel 대체. 숫자 Priority + 헤더.
- **EPP (Endpoint Picker / Inference Scheduler)**: 게이트웨이가 호출하는 ext-proc 확장. 파이프라인 **Filter**(과부하 제외) → **Scorer**(PrefixCache/KvCacheUtilization/QueueDepth/LoRAAffinity 가중합) → **Picker**(MaxScore).

## 6. Prefill/Decode 분리 (★)
- **이유**: Prefill=프롬프트 병렬 처리, **compute-bound**(컴퓨트 90%+) / Decode=토큰 순차 생성, **memory-bandwidth bound**(GPU 활용 20-40%). 자원 프로파일이 달라 분리하면 각각 독립 스케일·최적화.
- **KV cache 전송**: vLLM의 KV Connector API + **NVIDIA NIXL**로 prefill GPU→decode GPU KV cache를 **RDMA(InfiniBand/RoCE)/NVMe wire-speed** 이동(CPU 우회).

## 7. KV cache aware 라우팅 (★)
- 표준 LB는 무작위 분산 → cache locality 파괴. llm-d는 vLLM `KVEvents`로 **KV-Block Index(block-hash→pod)** 구성, **Prefix-Cache Scorer**가 "요청 prefix가 어느 Pod에 있는지"로 affinity 스코어 → load-aware와 결합.
- **Approximate**(기본, 인덱싱 서비스 불필요) vs **Precise**(KVEvents 직접 구독, 정확).

## 8. 연동 / 전제조건
- 게이트웨이: **Istio 1.27.0+** 또는 kgateway(GIE Gateway API CRD 필요). 3.4 Gateway API OIDC 직접 인증 GA.
- 하드웨어: GPU 노드 + NVIDIA GPU Operator, HF 토큰. **OCP 4.20+**. P/D 분리는 RDMA 네트워크 전제.
- MaaS가 앞단에 얹혀 거버넌스 → [33-MaaS](33-MaaS.md).

## 9. 운영 함정
- GIE API group 졸업으로 변경(`x-k8s.io`→`k8s.io`) — YAML 호환.
- InferenceObjective는 아직 Alpha.
- P/D 분리는 RDMA 네트워크(InfiniBand/RoCE) 필수.

## 10. 출처
- 개요: https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview
- GIE GA migration: https://gateway-api-inference-extension.sigs.k8s.io/guides/ga-migration/
- KV-cache routing: https://developers.redhat.com/articles/2025/10/07/master-kv-cache-aware-routing-llm-d-efficient-ai-inference

## 11. 미확인/주의
- 3.4 핀 GIE 정확 버전, InferencePool EPP 참조 필드 GA 명칭.
