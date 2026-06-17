---
title: Inference at Scale Sales Tactic (PPTX) 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - inference
  - sales
  - maas
source: Customer facing deck Inference at Scale Sales Tactic CY26.PPTX
---

# Inference at Scale — Sales Tactic CY26 (PPTX) 정리

> 원본: `Customer facing deck Inference at Scale Sales Tactic CY26.PPTX` (18 슬라이드). 고객용 추론 영업 덱.
> 상위 맥락: [00-인덱스](00-인덱스.md) / 기술 심화는 [03-AI-Inference-기술개요](03-AI-Inference-기술개요.md)

---

## 핵심 슬로건

**"Any model, any accelerator, any cloud — Red Hat AI: Fast and efficient inference, anywhere"**

## 슬라이드 흐름

1. **모델 선택지 폭발** (S2) — 2년간 OSS 모델 급증 타임라인: Llama(2023.3) → Mistral/Granite → Llama 3 → DeepSeek-R1(2025.1) → Llama 4·Qwen3(2025.4) → Kimi K2(2025.7) → OpenAI gpt-oss(2025.8).
2. **LLM 워크로드 특수성** (S3) — GPU 실행 / 비균일 프롬프트 / stateful·캐싱 이득.
3. **Red Hat AI 4대 가치** (S4) — 추론·데이터연결·하이브리드스케일·에이전트.
4. **토큰 소비자 → 모델 제공자** (S5) — MaaS로 자원효율↑. Any model/accelerator/cloud, 단순 소비, 자원공유 비용↓, 중앙 거버넌스.
5. **Enterprise GenAI Inference 스택** (S6) — Model as a Service / AI Gateway / Distributed Inference Framework / Models / Inference Server / Accelerators (GPU·Instinct·TPU Pods).
6. **하이브리드 추론 엔진** (S7) — vLLM이 핵심 모델 × 핵심 가속기(GPU/Instinct/Gaudi/TPU/Neuron/Spyre) 지원, 목록 계속 확장. gpt-oss 포함.

## 영업 핵심 수치 (Inference Server)

### 오픈소스 리더십 (S8)
- vLLM 코어·상위 상업 컨트리뷰터.
- **Neural Magic(Red Hat 인수)** 기여로 vLLM 부스트, 업계 호평.
- LinkedIn(2025.8), Databricks(Ray Summit 2024) 사례. Red Hat 협업으로 **TPOT(토큰당 시간) 7% 개선**.

### Model Catalog (S9)
- 프로덕션 준비 모델 발행: 타입/제공자/성능 필터, Red Hat 스캔·서명, 컨테이너화, 버전관리, **수백 시나리오 검증**, 정확도 유지 압축본.
- (디스클레이머: 스캔·서명·컨테이너화·버전관리는 **구독** 시에만. 업스트림 HF 레포는 무료.)

### 압축 모델 효과 (S10)
- **GPU 시간 40%+ 절감**
- **정확도 95~99% 유지** (베이스라인 대비 집중 튜닝·수천 시나리오)
- HuggingFace 다운로드 **1,600만+** (3rd party 압축모델)
- 고객은 자기 모델도 Red Hat 툴로 압축 가능.

### 분산 추론 / llm-d (S11~S12)
- disaggregated serving으로 **달러당 성능** 개선, inference-aware 로드밸런서로 지연 개선, 검증된 배포경로로 운영 단순화.
- **llm-d: SLA 제약 하 베이스라인 2배 QPS** (Llama 3.1 70B FP16, TP2·4 replicas, ISL 8000/OSL 100, P95 TTFT ≤2s) → **기존 인프라 용량 2배**.

### MaaS (S13)
- 모델을 더 넓은 사용자에 서비스로 제공. IT 중앙 서빙(GPU 풀, 큐레이트 모델, API Gateway 노출), 개발자 API 소비, 공유자원으로 비용↓(접근정책·차지백·쿼터).

## 고객사례 (S14)

- **북미 대형 금융사(FSI)** — 보안·온프렘 Gen AI 필요. 기존 OpenShift 고객 → OpenShift AI 확장, NVIDIA GPU. 결과: 전용 보안 온프렘 인프라, 통합 컨테이너 플랫폼(재현성·통제), 하이브리드 검증경로, 신용평가·계약협상 효율화, 단순한 추론 런타임.

## CTA (S15~S18)

- **Red Hat AI Inference Server**: 하이브리드 추론 런타임 + 모델 최적화. 모든 Red Hat 제품 인증, non-Red Hat Linux/k8s에도 배포(3rd party 지원정책).
- 서비스: AI Platform Foundation / AI Incubator / TAM / AI Assessment / Training & Certification / Consulting.
- 트라이얼: red.ht/ai-inference-server-trial, RHELAI-trial, RHOAI-trial.
- 인터랙티브 데모: red.ht/InferenceBenchmark, intro-llm-d, model-optimization, maas-pattern (redhat.com/interactive-experiences).

## 메모

- 04는 **수치·증거 중심 영업 덱**. 03(기술 심화)과 짝. 토킹포인트는 [00-인덱스](00-인덱스.md) §수치에도 집계.
