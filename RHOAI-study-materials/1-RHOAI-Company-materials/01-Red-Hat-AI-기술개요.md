---
title: Red Hat AI Technical Overview 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - rhoai
  - inference
  - agentic
source: Red Hat AI Technical Overview.PDF
---

# Red Hat AI Technical Overview 정리

> 원본: `Red Hat AI Technical Overview.PDF` — Red Hat AI 전반을 가장 폭넓게 다루는 기술 덱.
> 상위 맥락: [00-인덱스](00-인덱스.md)

---

## 1. 왜 어려운가 (문제 정의)

- 프로덕션 AI 구축은 환경/리소스 제약, 데이터 프라이버시, 워크플로 관리 등으로 어렵다.
- 모델 운영화에 **7~12개월(50%)**, **1년 이상(26%)** 소요 (Hidden Technical Debt, Sculley 2015 / Gartner).
- **LLM 워크로드는 클라우드 네이티브 앱과 다르다**:
  | 클라우드 네이티브 앱 | Gen AI 모델 |
  |---|---|
  | CPU에서 실행 | **GPU에서 실행** |
  | 균일·예측 가능한 요청 | **비균일 프롬프트/응답** |
  | 대부분 stateless | **stateful, 캐싱 이득** |
- 프로덕션엔 GuardRails, Evaluations, Datasets, Orchestration, Monitoring, MCP, Agents, Tool Calling 등 **스택 전체**가 필요 → 부담.

## 2. 플랫폼 구성 (Generative + Predictive + MLOps)

- **Model Development & Tuning**: Jupyter 워크벤치(as a service), 분산 학습/튜닝, 모델 커스터마이징 툴
- **Model Serving**: 서빙 런타임(vLLM, Custom, OVMS), 서빙 엔진 **KServe**, **llm-d**
- **Data & Model Pipelines**: Kubeflow Pipelines 기반 자동 파이프라인, 비주얼 에디터, 레지스트리, 실험 추적
- **Observability**: 성능/운영/품질 메트릭, **AgentOps**
- **공통**: 에이전트용 통합 API + MCP / Model Catalog(Granite + 3rd party) / llm-compressor·GuideLLM·lm-evaluation / Red Hat AI Inference Server(vLLM)
- **가속기**: PyTorch | FSDP | NVIDIA CUDA | AMD ROCm | Intel Gaudi | Google TPU

## 3. 추론 (Inference)

### vLLM
- 고처리량·저지연 LLM 추론 엔진. OpenAI 호환 API.
- **PagedAttention**(메모리 단편화 최소화), **continuous batching**(고처리량), **speculative decoding**, 양자화, multi-adapter.
- "vLLM이 모델 제작자와 가속 하드웨어를 연결" — Llama/Qwen/DeepSeek/Gemma/Mistral/Granite 등을 GPU/Instinct/TPU/Neuron/Gaudi/Spyre에서.

### 모델 최적화 (양자화)
- FP32 → FP16/INT8/INT4 저비트로 메모리·속도 개선.
- **DeepSeek-R1** 예: FP8/INT8 거의 완전 정확도 회복, INT4도 7B+ 모델 97%+ 회복, vLLM과 함께 **4배** 추론 성능, GPU 요구량 절감.
- 파이프라인: 모델 → **LLM Compressor**(GPTQ, SparseGPT, SmoothQuant) → 압축 체크포인트 → vLLM.

### 벤치마킹/평가
- **GuideLLM** — SLO 인지 벤치마킹(실 트래픽 시뮬레이션, throughput·latency).
- **lm-evaluation-harness** (EleutherAI) — 60+ 표준 학술 벤치마크, LoRA 등 어댑터 평가.
- 추론 트레이드오프: 정확도·응답성·비용 중 둘 최적화하면 셋째 악화. SLO로 의사결정(예: e-커머스 챗봇 TTFT 200ms/ITL 50ms, RAG는 정확도 우선).

### llm-d (분산 추론 / MaaS)
- Kubernetes 네이티브 분산 LLM 추론. vLLM 확장·상호운용.
- **마이크로서비스화**: prefill / decode / KV-cache 독립 스케일 → GPU 효율↑, 오버프로비저닝 방지.
- **Model-as-a-Service (MaaS)**: IT가 모델을 중앙 서빙, 개발자는 API로 소비. API 게이트웨이로 인증·rate limit·사용량 추적·차지백. "GPU 직접 접근이 아니라 엔드포인트가 필요".
- MaaS 스택: vLLM | llm-d | KServe + NVIDIA GPU Operator + Kueue + DCGM.

### KServe
- k8s 모델 서빙 사실상 표준(TF/PyTorch/ONNX/TensorRT/vLLM). Knative+Istio 옵션. **신규 LLMInferenceService CRD**로 llm-d 통합.

## 4. 모델을 데이터에 연결 (Connecting models to data)

- 커스터마이징 3종: **Prompting** / **RAG** / **Fine tuning**(InstructLab, OSFT, LoRA, QLoRA).
- "전체 기업 데이터의 1% 미만만 파운데이션 모델에 반영됨" → 사내 데이터 정렬 필요.
- **Real-World RAG 스택**: OpenAI 호환 API(/v1/responses, /v1/embeddings, /v1/vector_stores, /v1/files), 하이브리드 검색, 벡터DB(Milvus/PGVector), 평가(LM Eval Harness, RAGAS), **Llama Stack Server**.
- **Feature Store** — ML 피처 등록·관리·서빙(온라인 스토어).
- 커스터마이징 툴: **Docling**(문서 파싱), **SDG Hub**(합성데이터), **Training Hub**(SFT/Orthogonal SFT/LAB/GPT-OSS), **Evaluations**.
- **Kubeflow Trainer** 분산학습 — Kueue 연동, SFT, LoRA/QLoRA, DDP/FSDP, 내결함성.

## 5. 에이전트 AI (Agentic AI)

- 구성: The Engine(Llama Stack) / The Platform(AgentOps) / The Connectors(MCP, A2A) / The Experience(GenAI UI, starter kit, LangChain·LlamaIndex).
- 에이전트 시스템 요소: Tool 활용 · Planning/Execution · Reasoning · Orchestration · 통신 프로토콜.
- **MCP** — LLM이 외부 툴/데이터를 쓰는 플러그앤플레이 오픈 표준. 디커플드 아키텍처, 이식성.
- **Llama Stack** — 오픈소스 오케스트레이션 프레임워크. 통합 API(Inference, RAG, Agents). OpenAI 호환. LangChain/LangGraph/CrewAI/Deepset과 공존.
- **에이전트 성숙도 Level 0~4**: 단순규칙 → 정보검색 → 태스크 오케스트레이션 → 멀티도메인 → 멀티에이전트 시스템.
- **AI Hub**(플랫폼 엔지니어용 자산 관제) + **GenAI Studio**(AI 엔지니어용 실험 워크스페이스).
- 3.0에서 Deployments GA, AI Hub(모델→MCP·agents·prompts 확장), GenAI Studio.

## 6. 하이브리드 클라우드 스케일

- **GPU 과제**: 희소성/비용, 섀도IT, 단편화, 활용 블랙박스, 멀티테넌시 보안.
- 해법: GPU 풀링·통합 / 워크로드 right-sizing / 실시간 가시성 / 보안 멀티테넌시.
- **Kueue** — 지능형 워크로드 스케줄링(우선순위·선점·쿼터).
- **MIG (Multi-Instance GPU)** — NVIDIA GPU Operator로 하드웨어 분할(결정적 성능·격리).
- **DRA (Dynamic Resource Allocation)** — k8s API로 GPU 동적 요청.
- 안전/관찰성: bias·drift 탐지, Guardrails, 모델 모니터링, 정확도 평가, 실험 추적.
- 하드웨어: NVIDIA/AMD/Intel은 Red Hat AI 전반 지원. **Google TPU·IBM AIU는 Inference Server에서만**, IBM AIU는 RHOAI 3.0 예정, AWS Neuron은 로드맵.

## 키 용어

PagedAttention, continuous batching, speculative decoding, KV cache, prefill/decode 분리(disaggregated serving), MaaS, GuideLLM, lm-eval-harness, MIG, Kueue, DRA, KServe/LLMInferenceService, Llama Stack, MCP, A2A, AgentOps, Docling, SDG Hub, Training Hub.

## 메모

- 자료 중 **가장 종합적**. 04(영업덱)·03(추론심화)와 함께 보면 전체 그림 완성.
