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

> **이 문서는 입문·용어·GPS 로드맵 레이어다.** 컴포넌트 동작·MLOps 라이프사이클·GPU 통신 등 심화는 종합 SSOT [[03-rhoai-mlops-knowledge]], KServe 배포모드·오토스케일링 심화는 [[02-OpenShift-AI-플랫폼-아키텍처]] 참조.

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
