---
title: RHOAI 기초 용어 정리 (OCP 엔지니어 관점)
date: 2026-04-08
tags:
  - ai
  - rhoai
  - study
  - ocp
---

# RHOAI 기초 용어 정리 (OCP 엔지니어 관점)

> OCP를 아는 사람이 RHOAI/AI 플랫폼을 이해하기 위한 기반 지식 정리

> **이 문서는 입문·용어·GPS 로드맵 레이어다.** 컴포넌트 동작·MLOps 라이프사이클·GPU 통신 등 심화는 종합 SSOT [03-rhoai-mlops-knowledge](03-rhoai-mlops-knowledge.md), KServe 배포모드·오토스케일링 심화는 [02-OpenShift-AI-플랫폼-아키텍처](02-OpenShift-AI-플랫폼-아키텍처.md) 참조.

---

## 1. AI 모델이란

**AI 모델 = 거대한 수학 파일** (`.safetensors` 형식, 수GB~수백GB). GPU 메모리에 올려야 동작한다.

### 모델 유형

| 유형 | 하는 일 | 예시 |
|------|--------|------|
| **LLM** | 텍스트 생성 (대화, 요약, 코딩) | ChatGPT, Llama, Qwen, Granite |
| **Embedding** | 텍스트를 숫자 벡터로 변환 (검색용) | BGE, E5 |
| **ML** | 전통적 머신러닝 (분류, 예측) | XGBoost, sklearn |
| **OCR** | 이미지에서 글자 인식 | Tesseract |

---

## 2. 학습 vs 추론

| | **학습 (Training)** | **추론 (Inference/Serving)** |
|---|---|---|
| 뭐냐 | 모델을 만들거나 튜닝하는 과정 | 만들어진 모델에 질문하고 답 받는 과정 |
| OCP 비유 | **빌드(build)** | **런타임(deployment)** |
| GPU 사용 | 많이, 오래 (시간~일 단위) | 적게, 짧게 (밀리초~초 단위) |
| 실행 방식 | **배치 Job** (끝나면 종료) | **항상 띄워둔 서버** (API 요청 대기) |

---

## 3. RHOAI = OCP 위의 AI 전용 Operator 번들

OCP에 설치하면 AI 관련 컴포넌트를 한번에 관리해주는 Operator.

### OCP ↔ RHOAI 개념 매핑

| OCP 개념 | RHOAI에서 추가되는 것 |
|---------|-------------------|
| Operator | RHOAI Operator (AI 컴포넌트 전체 관리) |
| Deployment/Pod | InferenceService (모델 서빙 단위) |
| CronJob/Job | KFP Pipeline Run (학습/배포 자동화) |
| ResourceQuota | Kueue ClusterQueue (GPU 할당/스케줄링) |
| Route | KServe Endpoint (모델 API 엔드포인트) |
| ImageStream/Registry | Model Registry (모델 파일 버전 관리) |

---

## 4. 핵심 컴포넌트

### Kueue (큐이) — GPU 스케줄러

> OCP의 ResourceQuota를 GPU 학습 Job 전용으로 만든 것

- **ClusterQueue** = 클러스터 전체 GPU 풀 (예: H100 32장)
- **LocalQueue** = 팀별 큐 (예: 학습팀 60%, 추론팀 30%, 실험 10%)
- **Fair-Share** = 팀 간 GPU를 공정하게 나누는 정책
- **Preemption** = 우선순위 높은 Job이 낮은 Job을 밀어내는 것
- **ResourceFlavor** = GPU 종류별 그룹 정의 (`gpu-h100`, `gpu-a100`, `cpu-general`)

### KServe — 모델 서빙 자동화

> OCP의 Deployment + Service + Route를 AI 모델 전용으로 한방에 해주는 것

- `InferenceService` CRD 하나 만들면 → Pod + Service + Route 자동 생성
- 모델 파일을 S3에서 자동 다운받아 GPU에 로딩
- 오토스케일링(HPA) 내장

### vLLM — LLM 실행 엔진

> KServe가 "어떻게 띄울까"를 담당하면, vLLM은 "모델을 실제로 돌리는 엔진"

- LLM을 고성능으로 서빙하는 런타임
- OpenAI API 호환 (`/v1/chat/completions`) → 앱에서 호출하기 쉬움
- 핵심 최적화: Tensor Parallelism, 양자화, KV-cache 관리

### llm-d — 지능형 추론 라우터

> Istio 지능형 라우팅 + 메트릭 기반 가중치 조절을 합친 느낌

일반 로드밸런서(라운드로빈)와 달리 GPU 메모리 상태를 보고 라우팅:

- **Prefix-Aware 라우팅**: 같은 시스템 프롬프트 쓰는 요청 → 같은 Pod (캐시 공유)
- **Load-Aware 라우팅**: Pod GPU가 바쁘면 캐시 있어도 다른 Pod으로 (부하 분산 우선)
- **Prefill/Decode 분리**: 첫 응답 생성(무거움)과 이어서 토큰 생성(가벼움)을 다른 GPU에서 처리

스티키 세션과 비슷하지만 더 똑똑함. 스티키 세션은 세션 ID 기반 고정이지만, llm-d는 **GPU 메모리에 남아있는 KV-cache + 부하 상태**를 같이 본다.

### KFP v2 (Kubeflow Pipelines) — AI 파이프라인

> OCP의 Tekton Pipeline을 AI용으로 만든 것

- 학습 → 평가 → 모델 등록 → 배포를 파이프라인으로 자동화
- 각 Step이 별도 Pod으로 실행 (Tekton과 동일 개념)
- Elyra: 시각적 파이프라인 에디터 (GUI로 끌어다 놓기)

### Model Registry / AI Hub — 모델 관리

> OCP의 Quay/이미지 레지스트리에 대응

- **Model Catalog**: 사용 가능한 모델 검색 (HuggingFace 연동)
- **Model Registry**: 모델 파일 버전/메타데이터 관리 (MySQL 8.x 백엔드)
- **AI Hub**: Catalog + Registry + Deployments 통합 뷰 (RHOAI 3.3~)

---

## 5. 용어 사전

### GPU/하드웨어

| 용어 | 설명 |
|------|------|
| **GPU** | AI 연산 전용 하드웨어. CPU보다 병렬 처리 수백배 빠름 |
| **H100/A100** | NVIDIA GPU 모델명. H100이 최신, 더 비싸고 빠름 |
| **MIG** | Multi-Instance GPU. 하나의 GPU를 여러 개로 분할하는 NVIDIA 기능 |
| **DCGM** | Data Center GPU Manager. GPU 모니터링 도구 (사용률/온도/메모리) |
| **RDMA/RoCE** | GPU 간 고속 네트워크 통신 기술 |

### 모델 서빙/최적화

| 용어 | 설명 |
|------|------|
| **Tensor Parallelism (TP)** | 하나의 큰 모델을 GPU 여러 장에 쪼개서 올리는 기법 |
| **양자화 (Quantization)** | 모델을 압축하는 기법. FP16→FP8→INT4로 갈수록 작아짐. 성능은 약간 떨어짐 |
| **KV-cache** | LLM이 대화 맥락을 기억하는 GPU 메모리 영역 |
| **Serving Runtime** | 모델을 실행하는 컨테이너 런타임 (vLLM, OpenVINO 등) |
| **InferenceService** | KServe의 CRD. 모델 서빙 단위 (= Deployment 같은 것) |

### 성능 지표

| 용어 | 설명 |
|------|------|
| **TTFT** | Time To First Token. 질문 후 첫 글자 나올 때까지 시간 |
| **TPOT** | Time Per Output Token. 글자 하나 생성하는 데 걸리는 시간 |
| **TPS** | Tokens Per Second. 초당 생성 토큰 수 |
| **Latency** | 추론 요청부터 응답까지의 지연 시간. TTFT·TPOT로 측정 |
| **Throughput** | 단위 시간당 처리 가능한 추론 요청/토큰 수. 동시 사용자 많은 환경의 핵심 지표 |
| **ITL** | Inter-Token Latency. 연속 토큰 사이의 생성 지연 (≈ TPOT) |
| **RPS** | Requests Per Second. 초당 처리 요청 수 (처리량 지표) |
| **SLO / SLA** | 서비스 수준 목표(SLO: 내부 목표치)·협약(SLA: 외부 약속). LLM 서빙은 평균이 아니라 p95·p99로 약속 |
| **Jitter (지터)** | 지연시간의 변동성(들쭉날쭉함). TTFT·토큰 간격이 흔들리면 글자가 끊겨 나와 체감 품질 저하 |
| **p95 / p99 (백분위수)** | 응답시간 정렬 시 95%·99%가 이 값 이하. 평균이 가리는 "최악 경험"을 포착 (p99 ≥ p95 ≥ 평균) |

### 모델 관리

| 용어 | 설명 |
|------|------|
| **Fine-tuning** | 기존 모델을 특정 업무에 맞게 추가 학습시키는 것 |
| **RAG** | 외부 문서를 검색해서 LLM에 같이 넣어주는 기법 |

### LLM 입출력·추론 단계

| 용어 | 설명 |
|------|------|
| **Token** | LLM이 텍스트를 처리하는 최소 단위(단어/서브워드/문자). 비용·길이 산정 기본 단위 (영어 1단어 ≈ 1.3토큰, 한국어는 더 많음) |
| **Parameter** | 모델이 학습으로 조정한 가중치 값. 모델 크기 척도 (7B = 70억 개). 클수록 성능↑ 비용↑ |
| **Context Window** | 모델이 한 번에 처리 가능한 최대 토큰 수 (4K/8K/128K 등). 긴 문서 처리의 제약 |
| **prefix** | 모델 입력으로 주어지는 앞부분 텍스트(프롬프트·시스템 지시문·이전 대화). 토큰 배열 자체 |
| **prefill** | 입력 프롬프트를 한꺼번에 읽어 KV-cache를 채우는 추론 첫 단계 |
| **decode** | prefill 이후 답변을 토큰 하나씩 순차 생성하는 단계 |

> §4 llm-d의 "Prefill/Decode 분리"는 이 두 단계를 서로 다른 GPU에서 처리하는 것.

### 추론 유형

| 용어 | 설명 |
|------|------|
| **Real-time Inference** | 요청 즉시 응답하는 추론 방식. 챗봇·실시간 추천 등, Latency 최적화 필요 |
| **Batch Inference** | 대량 데이터를 일괄 처리하는 추론. 실시간 불필요 시 비용 효율적 (야간 리포트·대량 분류) |
| **Inference vs Reasoning** | 한국어로 둘 다 "추론"이나 다름. Inference=학습된 모델을 실행해 결과를 뽑는 행위(시스템·인프라). Reasoning=답 이전에 단계적으로 사고하는 능력(인지). reasoning 모델도 결국 inference로 실행됨 |

### 학습·튜닝 기법

| 용어 | 설명 |
|------|------|
| **Transfer Learning** | 한 도메인에서 학습한 지식을 다른 도메인으로 전이. Fine-tuning이 대표 사례 |
| **RLHF** | Reinforcement Learning from Human Feedback. 인간 피드백을 강화학습에 활용해 모델 정렬. ChatGPT 등이 사용 |
| **PEFT** | Parameter-Efficient Fine-Tuning. 전체 대신 극히 일부 파라미터만 학습하는 기법 총칭 |
| **LoRA** | Low-Rank Adaptation. 전체 가중치 대신 소규모 행렬만 학습. PEFT 대표 기법, 10~100배 적은 컴퓨팅 |
| **QLoRA** | LoRA + 양자화 결합. 단일 GPU로도 대규모 모델 파인튜닝 가능 |
| **SDG** | Synthetic Data Generation. AI가 학습용 데이터를 인공 생성. InstructLab 핵심 기술 |
| **LAB** | Large-scale Alignment for chatBots. InstructLab의 파인튜닝 방법론(SDG + 다단계 학습). Red Hat/IBM 차별화 |

### RAG·검색 구성요소

| 용어 | 설명 |
|------|------|
| **Embedding** | 텍스트/이미지를 고차원 수치 벡터로 변환. 의미 유사도 계산의 기반, RAG 핵심 구성요소 |
| **Vector Database** | 임베딩 벡터를 저장하고 유사도 검색하는 특화 DB (Milvus, pgvector, Pinecone 등) |
| **Semantic Search** | 키워드 매칭이 아닌 의미 기반 검색. 임베딩 + 벡터DB 기반 |
| **Chunking** | 문서를 RAG에 적합한 크기의 조각으로 분할. 청크 전략이 RAG 성능에 큰 영향 |
| **Reranking** | 1차 검색 결과를 관련성 기준으로 재정렬 (주로 Cross-Encoder). RAG 정확도 향상 |

### 품질·안전

| 용어 | 설명 |
|------|------|
| **Hallucination** | 모델이 사실과 다른 내용을 확신 있게 생성하는 현상. RAG로 완화 |
| **Guardrails** | 모델 출력을 제어·필터링하는 안전장치(유해 콘텐츠 차단 등). RHOAI는 TrustyAI Guardrails·Llama Guard로 구현 |

### MLOps 기초 (AI500 워크숍 용어집 통합)

| 용어 | 설명 |
|------|------|
| **MLOps** | AI 모델을 안정적·효율적으로 구축·배포·운영하기 위한 실천 방식·문화·도구 |
| **ETL** | Extract/Transform/Load. 데이터 수집·정제·저장 프로세스 |
| **EDA** | Exploratory Data Analysis. 데이터 패턴·문제를 이해하기 위한 탐색적 분석 |
| **Data Feature** | 모델에 쓰이는 개별·측정 가능한 데이터 속성 (나이·온도·거래금액 등) |
| **Feature Engineering** | 모델 성능 향상을 위해 피처를 생성·수정하는 작업 |
| **Feature Store** | 데이터 피처를 중앙에서 관리·제공하는 시스템 (RHOAI는 Feast) |
| **Neural Network** | 뉴런 다층 구조의 ML 모델. 높은 복잡도 처리 가능 |
| **Hyperparameter Tuning** | 레이어 수·학습률 등 모델 일반 설정을 조정해 성능 개선 |
| **Pipeline** | 데이터 처리·학습·배포의 자동화된 일련의 단계 |
| **Kubeflow** | Kubernetes에서 ML 워크플로를 관리하는 도구 모음 |
| **Argo CD** | 배포 자동화를 위한 GitOps 도구 |
| **Canary Deployment** | 전체 롤아웃 전 소규모 그룹에 새 모델을 먼저 배포 |
| **Shadow Deployment** | 사용자 영향 없이 새 모델을 병렬 실행해 검증 |
| **Data Drift** | 실제 데이터 분포가 학습 데이터와 크게 달라지는 현상 |
| **Bias Detection** | 모델의 불공정·의도치 않은 편향을 식별 (RHOAI는 TrustyAI) |
| **SHAP** | Shapley Additive Explanations. 각 피처가 예측에 기여한 정도로 모델을 설명 |
| **Counterfactuals** | 입력에 "what-if" 변화를 줘서 출력을 원하는 방향으로 바꿀 수 있는지 검증 |

### 모델 아키텍처·기초 개념

| 용어 | 설명 |
|------|------|
| **Predictive AI (예측 AI)** | 과거·실시간 데이터로 미래를 예측 (수요예측·사기탐지). 전통 ML(XGBoost·회귀) 기반 |
| **Generative AI (생성 AI)** | 학습 데이터로 새 콘텐츠(텍스트·이미지·코드)를 생성. Transformer 기반 |
| **Transformer** | 현대 LLM의 기반 구조. Decoder-only(GPT/Llama, 다음 토큰 예측), Encoder-only(BERT, 양방향), Encoder-Decoder(T5, 입력→출력 변환)로 나뉨 |
| **Self-Attention** | 문장의 모든 단어를 동시에 보며 각 단어가 다른 단어와 얼마나 관련 있는지 계산하는 메커니즘 |
| **Flash Attention** | Self-Attention의 제곱 복잡도 메모리 접근을 최적화해 속도·메모리를 개선하는 기법 |
| **Sliding Window Attention** | 근처 토큰에만 집중해 어텐션 복잡도를 줄이는 방식 (Mistral 등) |
| **Mixture of Experts (MoE)** | 여러 전문가(Expert) 네트워크 중 토큰마다 라우터가 일부만 활성화하는 효율적 아키텍처. 유효 파라미터 < 전체 파라미터. ※ "전문가"는 페르소나·역할 분담이 아니라 학습이 통계적으로 갈라놓은 하위 FFN 블록 (예: 8개 중 2개만 통과) |
| **State Space Model (SSM)** | Mamba 등, Transformer의 제곱 복잡도를 선형으로 줄인 대안 시퀀스 모델 |
| **Diffusion Model** | 노이즈를 점진적으로 제거해 이미지를 생성하는 아키텍처 |
| **Vision Transformer (ViT)** | 이미지를 패치로 잘라 단어처럼 Transformer에 넣는 비전 아키텍처 |
| **CLIP** | 이미지와 텍스트를 같은 벡터 공간에 배치해 의미 유사성을 학습하는 멀티모달 모델 |
| **Foundation Model** | 광범위 데이터로 사전학습된 범용 베이스 모델. 파인튜닝으로 도메인 적용 |
| **SLM (Small Language Model)** | 1~10B 규모의 컴팩트 모델. 제한된 컴퓨팅·특정 유스케이스에 최적 |
| **Frontier Model** | 특정 시점 최고 성능 모델(상대적 개념) |
| **Reasoning Model** | 강화학습 기반 chain-of-thought·자기검증·오류수정 능력을 갖춘 추론 특화 모델 |
| **Chain of Thought (CoT)** | 모델이 단계별로 사고를 전개하며 최종 답을 도출하는 추론 방식 |
| **AutoRegressive (자기회귀)** | 현재까지의 텍스트로 다음 토큰 확률분포를 계산해 반복 생성하는 LLM 메커니즘 |
| **Scaling Law** | 모델 크기·데이터를 키우면 성능이 예측 가능하게 향상되는 경험 법칙 |
| **Emergent Abilities** | 모델이 일정 규모를 넘으면 새 능력이 갑자기 나타나는 현상 |
| **Distillation (지식 증류)** | 큰 모델(교사)의 지식을 작은 모델(학생)로 압축. White-box(내부 logits 분포 모방, 정당) ↔ Black-box(출력 텍스트만 모방, 상용 API ToS 위반 소지 — 딥시크 논란) |
| **Gradient Descent / Backpropagation** | 손실을 최소화하도록 가중치를 반복 조정(경사하강)하며, 출력→입력 역방향으로 그래디언트를 계산(역전파)하는 학습 원리 |
| **CNN 기초 (Convolution/Pooling/Softmax)** | 필터로 로컬 피처 검출(합성곱) → 차원 축소(풀링) → 확률분포 변환(소프트맥스)하는 비전 신경망 구성 |

### 추론 최적화·분산

| 용어 | 설명 |
|------|------|
| **PagedAttention** | OS 페이지 테이블처럼 KV-cache를 동적 할당해 메모리 단편화를 줄이는 vLLM 핵심 기법 |
| **Continuous Batching** | 길이가 다른 요청을 실시간으로 배치에 채워 처리량을 높이는 스케줄링 |
| **Prefix Caching** | 같은 시스템 프롬프트 요청들이 KV-cache를 공유해 중복 계산을 줄이는 기법 |
| **Chunked Prefill** | 긴 프롬프트를 청크로 나눠 prefill 처리해 TTFT를 개선하는 기법 |
| **Speculative Decoding** | 작은 draft 모델이 토큰을 먼저 추측하고 큰 모델이 검증해 지연을 줄이는 기법 (EAGLE·Medusa 등) |
| **Disaggregated Serving (PD 분리)** | prefill(무거움)과 decode(가벼움)를 별도 GPU 그룹에서 처리하는 서빙 아키텍처 |
| **Pipeline Parallelism** | 모델 레이어를 여러 디바이스에 분할해 파이프라인으로 처리 |
| **Expert Parallelism (Wide EP)** | MoE 전문가들을 여러 GPU에 분산 배치하고 선택된 전문가로만 토큰을 보내는 희소 통신 |
| **Data Parallelism / FSDP / DDP** | 데이터를 GPU별로 나눠 학습. FSDP는 파라미터·옵티마이저 상태까지 샤딩, DDP는 모델 복제 |
| **MLA (Multi-head Latent Attention)** | KV-cache를 압축 공간으로 투영해 토큰 용량을 늘리는 기술 (DeepSeek 계열) |
| **MTP (Multi-Token Prediction)** | 한 번에 여러 토큰을 예측해 저부하 환경 속도를 높이는 기법 |
| **Structured Output** | JSON 스키마·정규식·문법으로 LLM 응답 형식을 강제하는 기능 |
| **Triton Inference Server** | NVIDIA 추론 서버. TensorRT·vLLM 등 백엔드를 프런트엔드 API로 제공 |
| **SGLang** | vLLM 계열에서 파생된 추론 런타임 |
| **RHAIIS** | Red Hat AI Inference Server. vLLM 기반에 엔터프라이즈 지원을 더한 Red Hat 제품 |

### 양자화·압축 (심화)

| 용어 | 설명 |
|------|------|
| **PTQ (Post-Training Quantization)** | 학습 후 모델을 양자화하되 캘리브레이션으로 정확도 손실을 최소화 |
| **Calibration (캘리브레이션)** | 대표 입력으로 양자화 스케일을 데이터 기반 최적화해 정확도를 보존 |
| **양자화 입도 (granularity)** | 몇 개 값이 하나의 scale을 공유하는지 정의 (Per-tensor/Channel/Group) |
| **가중치 표기 (W8A8/W4A16 등)** | W=가중치, A=활성값 비트 수. 예: W8A8(둘 다 8bit), W4A16(가중치 4bit·활성 16bit) |
| **SmoothQuant** | 활성값의 이상치를 가중치로 수학적 이전해 양자화를 쉽게 만드는 기법 |
| **AWQ** | Activation-aware Weight Quantization. 활성 패턴상 중요 채널을 보호하는 양자화 |
| **GPTQ** | GPU 최적화 int4 양자화 포맷 (vLLM/AutoGPTQ 지원) |
| **GGUF** | 로컬 실행 도구(llama.cpp/Ollama 등)의 표준 양자화 모델 포맷 |
| **Pruning (프루닝)** | 중요도 낮은 가중치·채널·필터를 제거해 모델을 경량화 |
| **Sparsity / 2:4 Structured Sparsity** | 일부 가중치를 0으로(희소화). 4개 중 2개 제거 방식은 NVIDIA Ampere+ 하드웨어 가속 지원 |
| **SparseGPT** | 구조적 희소성으로 50% sparsity를 달성하는 압축 알고리즘 |
| **Vector Quantization (VQ)** | 코드북의 최근접 벡터로 값을 대체하는 압축 방식 (KV-cache 압축 등) |
| **LLM Compressor** | HuggingFace 호환 양자화·압축 도구. vLLM 서빙용 모델 출력 (Red Hat AI) |

### GPU 공유·인터커넥트

| 용어 | 설명 |
|------|------|
| **MPS (Multi-Process Service)** | GPU를 SM 비율로 동시 공유하는 소프트 격리 방식 |
| **Time-slicing** | GPU를 시간 단위로 분할해 여러 워크로드가 번갈아 쓰는 방식 (높은 집적도, 격리 약함) |
| **MIG Adapter** | 요청한 MIG 타입이 없으면 상위 호환 타입으로 자동 배치하는 기법 |
| **DAS Operator (Dynamic Accelerator Slicer)** | Pod 요청 시점에 MIG 슬라이스를 동적 생성·삭제하는 NVIDIA 오퍼레이터 |
| **Noisy Neighbor** | 격리 부족으로 한 워크로드가 다른 워크로드 성능에 간섭하는 현상 (time-slicing 위험) |
| **Gang Scheduling** | 분산 학습에 필요한 GPU를 모두 확보할 수 있을 때만 Pod을 생성하는 스케줄링 |
| **Quota Borrowing** | 같은 Cohort 내 유휴 자원을 임시로 빌려 쓰고 반환하는 Kueue 기능 |
| **NVLink / NVSwitch / NVL72** | GPU 간 고속 직결(NVLink), 노드 내 패브릭으로 묶기(NVSwitch), 랙 72 GPU를 단일 시스템화(NVL72) |
| **GPUDirect RDMA / PCIe P2P** | GPU가 CPU를 거치지 않고 NIC·다른 GPU와 직접 데이터 교환 |
| **Accelerator (가속기)** | 대규모 행렬·텐서 연산을 CPU보다 빠르게 처리하는 전용 하드웨어 (GPU·TPU·NPU·Trainium/Inferentia 등). 수천 코어로 병렬 처리 |
| **HBM (High Bandwidth Memory)** | GPU의 초고대역폭 메모리 (모델 가중치 상주 영역) |
| **NPU (Neural Processing Unit)** | AI 워크로드 특화 프로세서 |
| **SM (Streaming Multiprocessor)** | GPU의 연산 유닛. 다수 스레드를 병렬 실행 |
| **DRA (Dynamic Resource Allocation)** | 특수 하드웨어(GPU 등)를 동적으로 요청·할당하는 Kubernetes API |
| **Scale-to-zero / Cold Start** | 요청 없으면 Pod을 0개로 축소(scale-to-zero), 복귀 시 초기화로 인한 첫 응답 지연(cold start) |

### 에이전트·도구

| 용어 | 설명 |
|------|------|
| **Agentic AI / Agentic Workflow** | LLM이 도구 호출 순서를 하드코딩 없이 자율 결정하는 시스템·워크플로 |
| **ReAct** | Reason→Act→Observe 반복으로 추론 과정을 추적 가능하게 하는 에이전트 루프 |
| **Agentic RAG** | 에이전트가 RAG 사용 여부를 자율 판단해 검색을 동적으로 적용하는 패턴 |
| **Tool Calling (Function Calling)** | LLM이 함수 메타데이터를 보고 호출할 도구·파라미터를 결정하는 능력 |
| **MCP (Model Context Protocol)** | LLM과 외부 도구/데이터를 연결하는 표준 프로토콜. 한 번 만든 MCP 서버를 여러 AI에서 재사용 |
| **MCP Server / Client** | 외부 시스템을 도구로 노출하는 엔드포인트(서버) ↔ 도구를 발견·호출하는 런타임(클라이언트) |
| **Multi-agent** | 여러 에이전트가 협업·분담해 복잡 작업을 수행하는 구성 |
| **HITL (Human-in-the-loop)** | 위험 동작 전 사람이 확인·승인하는 제어 패턴 |
| **Tool Schema** | 도구의 이름·설명·파라미터·반환형식을 JSON으로 정의한 메타데이터 |

### 프롬프트·생성 제어

| 용어 | 설명 |
|------|------|
| **System / User Prompt** | 행동·맥락을 정의하는 개발자 작성 지시(System) ↔ 사용자가 입력하는 질문(User). System이 우선순위 높음 |
| **Prompt Engineering** | 표현·형식·예시·단계적 사고를 조정해 유용한 출력을 끌어내는 설계 |
| **Temperature** | 생성 무작위성 다이얼. 0=결정적, 높을수록 다양·예측불가 |
| **Few-shot Prompting** | 예시 몇 개를 제공해 패턴을 학습시켜 유사 작업을 수행하게 하는 기법 |
| **맥락 주입 (Context Injection)** | 프롬프트에 정보를 직접 넣어 답변을 유도(대화 종료 후 사라짐) |

### RAG 심화

| 용어 | 설명 |
|------|------|
| **Ingestion / Query Pipeline** | 문서 수집→청킹→임베딩→벡터DB 저장(배치) ↔ 질문 임베딩→검색→프롬프트 조립→추론(실시간) |
| **Hybrid Search** | 의미 검색(벡터 유사도)과 키워드 검색(BM25)을 결합해 정확도·리콜을 동시 확보 |
| **RAFT (Retrieval-Augmented Fine-Tuning)** | 관련·무관 컨텍스트가 섞인 데이터로 파인튜닝해 검색 문서 활용력을 높이는 기법 |
| **Point-in-Time Correctness** | 그 시점에 알 수 있던 값만 사용해 학습 데이터 누수를 막는 Feature Store 원리 |

### 평가·관찰성

| 용어 | 설명 |
|------|------|
| **LLM-as-Judge** | 정답이 정형화되지 않은 생성물을 다른 LLM으로 채점하는 평가 방식 |
| **Evals (Expectations/Scorers)** | 입력별 기대 출력을 정의(Expectations)하고 실제 출력을 채점(Scorers)해 회귀를 감지 |
| **lm-evaluation-harness** | 업계 표준 학술 벤치마크로 모델 능력(양자화 후 등)을 검증하는 평가 도구 |
| **GuideLLM** | TTFT/ITL/RPS/Throughput 등 LLM 전용 지표를 측정하는 벤치마킹 도구 (Red Hat AI) |
| **Champion/Challenger (A/B)** | 현 프로덕션(Champion)과 신버전(Challenger)을 동시 배포해 성과로 승격 결정 |
| **OpenTelemetry** | 로그·메트릭·트레이스를 표준화하는 관찰성 표준 (Collector·Tempo·Loki 연동) |
| **OSD (Over-Saturation Detection)** | 벤치마킹 중 서버 과포화를 조기 감지해 테스트를 자동 중단 |

### 안전·가드레일

| 용어 | 설명 |
|------|------|
| **Prompt Injection** | 사용자 입력에 악의적 지시를 끼워 모델의 의도된 행동을 우회하려는 공격 |
| **Jailbreak** | 안전 제약을 우회해 모델이 금지된 출력을 내도록 유도하는 공격 |
| **Guardrails 계층** | 입력(인젝션)·도구 호출·출력 위반을 각각 검사하는 defense-in-depth 안전 구조 |
| **Llama Guard / Prompt Guard / Shields** | 유해 콘텐츠 분류(Llama Guard)·인젝션 탐지(Prompt Guard)를 입출력에 적용하는 가드레일(Shields) |
| **NeMo Guardrails** | 요청/응답을 LLM 도달 전후로 검사해 할루시네이션·인젝션·혐오를 차단하는 미들웨어 (Colang DSL) |
| **PII 탐지** | 개인식별정보(주민번호·이메일 등)를 자동 감지·마스킹 |
| **Toxic Output (HAP)** | 혐오·욕설·비속어 등 유해 출력 (Granite Guardian 등으로 탐지) |

### MLOps·파이프라인 (심화)

| 용어 | 설명 |
|------|------|
| **GitOps** | Git을 desired state의 단일 진실 원천으로 삼아 ArgoCD가 지속 reconciliation하는 배포 패러다임 |
| **Reconciliation** | 선언된 Git 상태와 실제 클러스터 상태를 지속 비교해 어긋나면 자동 적용 |
| **Continuous Training (CT)** | 신규 데이터·성능 저하 시 자동으로 재학습·서빙하는 MLOps Level 1+ 프로세스 |
| **Data Validation** | 파이프라인에서 데이터 스키마·통계·품질을 확인해 입력 안정성을 보장 |
| **Metadata Store** | 데이터셋·모델·실험의 계보·버전·성능 메타데이터를 중앙 저장 |
| **Training-Serving Skew** | 학습과 추론의 피처 정의·전처리 차이로 성능 불일치가 생기는 문제 |
| **Inner Loop / Outer Loop** | 노트북 대화형 실험(inner) ↔ 자동 파이프라인 재현(outer) |
| **DVC (Data Version Control)** | Git 위에 대용량 데이터·모델·파이프라인을 버전 관리해 재현성 확보 |
| **ModelScan / Serialization Attack** | 모델 파일에 주입된 악성 코드(로드 시 자동 실행)를 로드 전 탐지하는 보안 스캔 |
| **GenAIOps** | 생성 AI 앱의 개발·테스트·배포·운영을 자동화·표준화하는 운영 방식 |

### RHOAI 컴포넌트·CRD

| 용어 | 설명 |
|------|------|
| **DataScienceCluster (DSC)** | 설치할 RHOAI 컴포넌트를 Managed/Removed로 토글하는 단일 CRD (v2) |
| **DSCInitialization (DSCI)** | ServiceMesh·신뢰 인증서 등 클러스터 전역 설정을 정의하는 CR |
| **AcceleratorProfile / 하드웨어 프로파일** | Workbench·InferenceService가 선택하는 GPU 타입별 리소스 할당 정책(NodeSelector+쿼터) |
| **LLMInferenceService** | KV-cache 인식 캐시 라우팅으로 분산 LLM 추론을 관리하는 llm-d용 CR |
| **LlamaStack / LlamaStackDistribution** | Inference/RAG/Agents/Safety/Tools 통합 API 서버(OpenAI 호환). CRD로 선언형 배포 |
| **Data Connection** | S3 버킷을 Workbench에 네이티브 마운트해 모델·인덱스에 접근하게 하는 CR |
| **Data Science Pipeline (DSP)** | RHOAI의 KFP 통합 서비스. Tekton(v1.x)/Argo Workflows(v2.x)를 백엔드로 사용 |
| **Training Operator / Training Hub** | 단일노드 학습을 PyTorch/TF 분산학습으로 수평확장(Operator). SFT/LoRA 학습 모듈(Hub) |
| **RHCL + Limitador + Authorino** | Red Hat Connectivity Link로 Inference Gateway의 인증(Authorino)·rate limit(Limitador)·TLS를 Gateway API로 통합 |
| **Cluster Observability Operator** | KServe 추론 메트릭·모델 성능을 수집해 대시보드로 가시화 |
| **InstructLab** | 커뮤니티 기반 모델 정렬·파인튜닝 플랫폼 (SDG + LAB 방법론, Granite 대상) |
| **SDG Hub** | 문서·가이드라인으로 학습용 합성 데이터를 생성하는 도구 (수작업 라벨링 불필요) |
| **Docling** | PDF·문서의 구조(섹션·표·수식)를 보존해 머신리더블 형식으로 변환하는 전처리기 |
| **TrustyAI** | 모델 설명성(SHAP/LIME)·편향 탐지·공정성·drift를 제공하는 책임 AI 도구 |
| **Validated Patterns** | Red Hat 검증 레퍼런스 아키텍처를 코드(Helm/Ansible/GitOps)로 제공하는 프레임워크 |

### 엔터프라이즈·거버넌스

| 용어 | 설명 |
|------|------|
| **MaaS (Models-as-a-Service)** | 모델을 게이트웨이+토큰 과금으로 구독형 서비스화하는 운영 모델 |
| **Inference Gateway** | 서빙 앞단 API 게이트웨이. 인증·사용량 측정·rate limit·라우팅 처리 |
| **GPUaaS (GPU-as-a-Service)** | GPU를 공유 풀로 묶어 팀·네임스페이스가 API 뒤 추론 엔드포인트로 사용 |
| **Token Economy / 토큰 과금** | 백만 토큰당 단가로 AI 비용을 측정·청구하는 경제 모델 |
| **Chargeback** | 부서·팀별 토큰 사용량을 측정해 비용을 귀속하는 내부 청구 |
| **Sovereign AI** | 데이터·모델·추론을 통제권 내(온프렘·특정 지역·신뢰 클라우드)에서 관리하는 전략 |
| **Data Residency / Data Lineage** | 민감 데이터의 관할 이탈 금지(residency) ↔ 데이터 출처·변환 이력 추적(lineage) |

### Red Hat AI 제품 라인업

> 같은 vLLM 엔진을 공유하되 "어디에 배포하느냐"로 제품이 나뉨. 작게 시작(서버 1대) → 전사 확장.

| 용어 | 설명 |
|------|------|
| **Red Hat AI Inference Server (RHAIIS)** | vLLM 기반 추론 런타임(단독 제품). RHOAI·RHEL AI에 공통 부품으로 포함 |
| **RHEL AI** | 단일 서버용 모델 어플라이언스. immutable RHEL 이미지(image mode)로 OS+AI 패키징, air-gapped 강점, indemnified Granite 포함 |
| **RHOAI (OpenShift AI)** | 분산 k8s용 통합 AI 플랫폼 (MLOps 전주기) |
| **RHAIE (AI Enterprise)** | RHOAI 기반 전사 확장·거버넌스 통합 배포판 |

### 개발도구·에코시스템

> 일반 AI/RHOAI 플랫폼 용어는 아니지만 데모·실습 자료에 자주 등장하는 코드 에이전트·로컬 AI 개발도구.

| 용어 | 설명 |
|------|------|
| **Continue** | VS Code/JetBrains AI 코딩 플러그인 (코드 생성·리팩토링) |
| **Dev Spaces** | 클라우드 IDE 개발환경 (LLM 엔드포인트 네이티브 접근) |
| **Lola** | AI 컨텍스트(스킬·MCP·지침) 패키지 매니저 (Helm처럼 AI 자산 버전관리) |
| **Bunsen** | 테스트 결과를 AI로 분석해 flaky 테스트를 탐지하는 도구 |
| **LangGraph** | 그래프 기반 상태 오케스트레이션으로 복잡 에이전트 워크플로를 구성하는 프레임워크 |
| **Langflow** | MCP 노드·드래그앤드롭으로 에이전트 워크플로를 시각 구성하는 빌더 |
| **Podman AI Lab** | Podman Desktop 확장. 모델 카탈로그·플레이그라운드·레시피·BYOM 제공 로컬 AI 개발도구 |
| **RamaLama** | AI 모델·RAG 데이터를 OCI 이미지로 패키징·배포하는 도구 |
| **BYOM (Bring Your Own Model)** | 직접 만든 `.gguf` 모델을 import해 사용하는 기능 |
| **Quadlet** | Podman 컨테이너를 systemd 서비스로 전환하는 제너레이터 |
| **LangChain.js / ChatOpenAI** | LLM 오케스트레이션 JS 라이브러리와 OpenAI 호환 API 클래스 |
| **llamacpp_python** | llama.cpp의 Python 바인딩 (OpenAI 호환 로컬 서빙) |
| **Sentence-Transformers** | 문장 수준 임베딩을 생성하는 라이브러리 (RAG 청크 임베딩) |
| **React Chatbotify** | 챗봇 프론트엔드 UI 라이브러리 |
| **LM Studio / MLX** | GUI 로컬 LLM 실행 도구 / Apple Silicon 최적화 로컬 프레임워크 |
| **Open WebUI / AnythingLLM** | 웹 기반 LLM·RAG UI 애플리케이션 |
| **Attu** | Milvus 벡터DB 관리·시각 탐색 웹UI |
| **Gradient UI** | RAG 앱 테스트·품질검증 프로토타이핑 UI |

### 상용 서비스·특정 모델

> 특정 벤더의 상용 LLM 서비스/제품 및 자료에 등장하는 구체 모델명.

| 용어 | 설명 |
|------|------|
| **ChatGPT / OpenAI API** | 상용 LLM 서비스 및 API |
| **AWS Bedrock** | 클라우드 관리형 LLM 서비스 |
| **Tavily** | 상용 실시간 웹검색 API (에이전트 도구) |
| **LiteLLM Proxy** | 여러 백엔드(로컬 vLLM/OpenAI/Bedrock)를 단일 OpenAI 호환 API로 통합하는 경량 프록시 |
| **Granite** | Red Hat/IBM 오픈소스 LLM 시리즈 |
| **Llama 3.2** | Meta 오픈 LLM |
| **Gemma 4** | Google 오픈 LLM |
| **DeepSeek-R1** | DeepSeek 추론 특화 모델 (MLA·MTP 기술 출처) |
| **벡터DB 제품군** | Milvus·pgvector·FAISS·Chroma·EDB·Redis·Elasticsearch 등 벡터 저장·검색 제품 (→ Vector Database 항목 참고) |

### Red Hat 제품 상태

| 용어 | 설명 |
|------|------|
| **GA** | General Availability. 정식 지원 |
| **TP** | Tech Preview. 베타 수준. 프로덕션 SLA 미보장 |
| **DP** | Dev Preview. 알파 수준. 평가용 |
| **GPS** | Guided Professional Services. Red Hat 컨설팅 서비스 |

---

## 6. 외부 의존성 (RHOAI에 미포함, 별도 준비)

| 의존성 | 용도 |
|--------|------|
| MySQL 8.x | AI Hub (Model Registry) 백엔드 |
| PostgreSQL 12+ | Kubeflow Pipelines 메타데이터 저장 |
| S3 호환 스토리지 | 모델 파일 + 파이프라인 아티팩트 저장 |
| NVIDIA GPU Operator | GPU 드라이버 관리 |
| Cert Manager | TLS (RHOAI 3.3 신규 필수) |
| Serverless (Knative) | KServe 오토스케일링 |
| Service Mesh (Istio) | Canary 배포, Failover (선택) |

---

## 7. GPS 실무를 위한 학습 우선순위

> W은행 프로젝트에서 GPS 담당 영역 기준

### 학습 로드맵

| 순위 | 영역 | 이유 | 난이도 |
|------|------|------|--------|
| **1** | Kueue | 완전 새로운 것, Task 비중 최대 | 중 |
| **2** | KServe + vLLM | 배포 핵심, 파라미터 튜닝 | 중 |
| **3** | DCGM/vLLM 메트릭 | OCP 모니터링 확장 | 하 |
| **4** | AI Hub | 거의 DB+스토리지 연결 수준 | 하 |

Kueue랑 KServe 두 개만 확실히 잡으면 프로젝트 자료의 70%는 읽힌다.

---

### 7.1 Kueue 심화 — GPS 작업 비중 최대 (16 Tasks)

OCP에 없는 완전히 새로운 컴포넌트.

**CRD 4종 관계:**
```
ResourceFlavor  →  "이 노드그룹은 H100 4장짜리다" 정의
ClusterQueue    →  ResourceFlavor를 묶어서 전체 GPU 풀 구성
LocalQueue      →  팀별로 ClusterQueue의 몫을 나눠줌
Cohort          →  ClusterQueue끼리 GPU를 빌려주고 빌려오는 그룹
```

**핵심 정책 3가지:**
- **Fair-Share**: 가중치 기반 배분 (weight:2 vs weight:1 → 2:1 비율)
- **Preemption**: 우선순위 높은 Job이 낮은 걸 쫓아내는 정책 (quota-level vs topology-level 중 택1)
- **PriorityClass**: Critical/High/Normal/Low 4단계 — K8s 기본 PriorityClass랑 같은 개념

**OCP 지식과 연결:**
- ResourceQuota → ClusterQueue의 `resourceGroups`
- LimitRange → ResourceFlavor의 노드 셀렉터
- PriorityClass → 그대로 동일

---

### 7.2 KServe + vLLM 심화 — 모델 배포 실무

**KServe는 OCP 지식으로 80% 이해 가능:**

```yaml
# Deployment + Service + Route + HPA를 한번에 만드는 CRD
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-70b
spec:
  predictor:
    model:
      modelFormat: vLLM
      runtime: vllm-runtime    # ← ServingRuntime (컨테이너 이미지 정의)
      storageUri: s3://models/llama-70b  # ← 모델 파일 위치
      resources:
        limits:
          nvidia.com/gpu: "8"  # ← GPU 8장 요청
```

**vLLM 핵심 파라미터:**

| 파라미터 | 의미 | OCP 비유 |
|---------|------|---------|
| `--tensor-parallel-size 8` | GPU 8장에 모델 분산 | 없음 (AI 전용) |
| `--gpu-memory-utilization 0.9` | GPU 메모리 90%까지 사용 | requests/limits 비율 같은 느낌 |
| `--max-num-seqs 256` | 동시 처리 요청 수 | maxSurge 같은 느낌 |
| `--quantization fp8` | 모델 압축 방식 | 없음 (AI 전용) |

**ServingRuntime = 컨테이너 이미지 템플릿:**
- vLLM Runtime (LLM용) — 기본 제공
- OpenVINO Runtime (경량 ML용) — 기본 제공
- Custom Runtime (OCR 등) — **GPS가 YAML 설계해줘야 함**

---

### 7.3 모니터링 심화 — OCP 지식 + AI 메트릭

OCP 모니터링은 이미 아는 영역. 추가로 알아야 할 건 AI 전용 메트릭.

**GPU 레이어 (DCGM Exporter):**
```
DCGM_FI_DEV_GPU_UTIL      → GPU 사용률 (%)
DCGM_FI_DEV_FB_USED       → GPU 메모리 사용량
DCGM_FI_DEV_GPU_TEMP      → GPU 온도
```
- node-exporter처럼 DaemonSet으로 돌아감
- **함정**: 노드 레벨만 제공 → Pod별 GPU 추적하려면 커스텀 PromQL 필요

**모델 레이어 (vLLM 메트릭):**
```
vllm:time_to_first_token_seconds   → TTFT (첫 응답까지 시간)
vllm:time_per_output_token_seconds → TPOT (토큰당 생성 시간)
vllm:num_requests_running          → 현재 처리 중 요청 수
vllm:gpu_cache_usage_perc          → KV-cache 사용률
```
- ServiceMonitor로 수집 (OCP랑 동일)
- Grafana 대시보드 구성이 GPS 일

**알림 규칙 예시:**
```yaml
- alert: LLMHighLatency
  expr: vllm:time_to_first_token_seconds > 5
  for: 5m
  labels:
    severity: warning
```

---

### 7.4 AI Hub — 가볍게만

개념만 알면 되고, 실제 구축은 단순한 편:

- MySQL 8.x 연결
- S3 백엔드 연결
- 메타데이터 스키마 정의 (모델명, 버전, accuracy 등)
- RBAC 설정

OCP에서 Quay 구축하는 것과 난이도 비슷.
