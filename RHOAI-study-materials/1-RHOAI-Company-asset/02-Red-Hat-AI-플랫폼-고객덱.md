---
title: Red Hat AI Platform Customer Deck 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - rhoai
  - sales
source: Red Hat AI Platform _ Customer Deck.PDF
---

# Red Hat AI Platform — Customer Deck 정리

> 원본: `Red Hat AI Platform _ Customer Deck.PDF` (최신 업데이트 2026-02). 고객/영업 발표용 덱 + 제품 슬라이드 + 고객사례.
> 상위 맥락: [[00-인덱스]] / 기술 상세는 [[01-Red-Hat-AI-기술개요]]

---

## 1. 도입부 — 고객 채택 과제 3C

- **Cost** — 프런티어 모델 서비스는 엔터프라이즈 스케일에서 비용 과다.
- **Complexity** — 사내 데이터로 모델 튜닝은 비전문가에겐 너무 복잡.
- **Control** — 데이터 프라이버시·보안·지연 우려로 하이브리드 전략 선택.

## 2. Red Hat AI 개요 (4대 가치)

빠르고 유연·효율적 추론 / 모델-데이터 연결의 단순·일관 경험 / 에이전트 AI 가속 / 하이브리드 클라우드 스케일.
- Trusted·Consistent·Comprehensive 기반 + 하드웨어 가속(Physical/Virtual/Private/Sovereign/Public/Edge).
- **제품 4종**: Red Hat AI Enterprise / Inference Server / OpenShift AI / RHEL AI ([[00-인덱스]] 표 참고).

### 3.4 제품 업데이트 (덱 기재)
- **Inference**: AI 게이트웨이 MaaS, vLLM 모델·HW 확대, llm-d 요청 우선순위·배치추론, speculative decoding.
- **Models to Data**: Evaluation Hub(통합 평가 컨트롤 플레인), 실험추적, AutoRAG·AutoML.
- **Agentic**: 에이전트 ID·라이프사이클 관리, 에이전트 트레이싱·관찰성, 큐레이트 MCP 카탈로그·MCP 게이트웨이.
- **Platform**: prompt lab·registry, AI 안전·자동 레드티밍, MLflow 거버넌스.

## 3. 빠르고 유연한 추론

- 오픈소스 모델 폭발적 확장(2023 Llama → 2025 DeepSeek-R1, Llama 4, Qwen3, gpt-oss 등).
- 4단계 선택: 모델 선택(검증·최적화 카탈로그) → 추론 런타임(vLLM) → 하드웨어 → 스케일(llm-d).
- **Hugging Face의 Red Hat AI 레포**: 검증(GuideLLM·LM Eval Harness)·최적화(LLM Compressor) 모델. Transformers(Dense/MoE), 멀티모달, 임베딩, Vision.
- **MaaS**: 토큰 소비자 → 모델 제공자로 성장. 중앙 거버넌스·자원 공유로 비용↓.

## 4. 모델-데이터 연결 & 에이전트

- 기업은 사내 데이터 정렬 필요(1% 미만만 모델 반영). 검증모델 + 데이터 인제스트 + SDG + 정렬기법.
- 모듈형 커스터마이징: Data processing / Synthetic data / Training hub / Evaluate.
- **Gen AI → AI Agent → Agentic AI** 진화: 생성자 → 실행자 → 관리자(다중 에이전트 협업).
- Red Hat AI 에이전트 기반: **ogx (구 Llama Stack)** 내장 프레임워크 + MCP, LangChain/CrewAI 통합, 에이전트를 마이크로서비스로 운영.
- **MCP** 4요소: Creation Guide / Try before you buy(Playground) / AI assets / Llama Stack tool calling.
- 전용 대시보드: **AI hub** + **Gen AI studio**.

## 5. 하이브리드 스케일 + 안전

- 기존 투자 활용(통합 AI 플랫폼·개발·MLOps/GenAIOps·모니터링). Day 2 운영(거버넌스·자동화).
- 하드웨어: GPU/Instinct/Xeon/TPU/AIU/Neuron — *NVIDIA·AMD·Intel 전체 지원, TPU·AIU는 Inference Server only, AIU는 RHOAI 3.0, Neuron 로드맵.*
- 안전/관찰성: bias·drift 탐지, Guardrails, 모델 모니터링, 정확도 평가, 실험 추적.

## 6. Why Red Hat AI? (가치)

- **Flexibility**(최신 오픈소스 접근) · **Choice**(오픈 생태계) · **복잡성 추상화**.
- 가치: 효율 증가 / 단순한 경험 / 어디든 배포.
- 파트너 생태계(하드웨어·클라우드·SI·배포·앱/데이터) — catalog.redhat.com.

## 7. Red Hat AI Services (도입 여정)

**Strategy → Learn → Validate → Deploy → Scale**
- Discovery/AI Assessment → 팀 정렬·교육 → **AI Incubator**(첫 유스케이스 공동검증, 레지던시형 컨설팅) → AI Platform Foundation(파일럿→프로덕션) → Operationalize(중앙팀, 모니터·최적화).
- **TAM** (Technical Account Management) — yearly 구독, 보안·로드맵·운영 advisory.
- 교육: AI010(Inference Tech Overview), AI067(Tech Overview), AI296(RHEL AI Granite), AI500(MLOps Enablement), AI501(GenAIOps), AI267/EX267(개발자 인증). **Red Hat AI Foundations** 무료 학습경로.
- 무료 60일 트라이얼: red.ht/RHELAI-trial, RHOAI-trial, ai-inference-server-trial, RHAIE-trial.

## 8. 제품 슬라이드 요약

- **Red Hat AI Inference Server**: vLLM 기반, 모든 가속기/환경. 모델 압축 + 분산추론 + HF 레포. OpenShift AI·RHEL AI에 포함. (Red Hat = OSS GenAI 추론 리더, vLLM 코어 커미터 7명, llm-compressor, 사전최적화 모델.)
- **Red Hat AI Enterprise**: 통합 엔터프라이즈 AI 플랫폼. 통합 라이프사이클(predictive/gen/agentic), 지능형 스케일, 거버넌스·신뢰, 하이브리드 민첩성. AI Gateway·Inference at scale·Security·Observability·Model/Agent catalog.
- **Red Hat OpenShift AI (RHOAI)**: 예측+생성 단일 플랫폼. 통합 MLOps/LLMOps, 모델개발·튜닝(LoRA/QLoRA/SDG), vLLM&llm-d, Trust&Guardrails, AgentOps(Llama Stack+MCP). air-gapped 지원.
- **Red Hat Enterprise Linux AI (RHEL AI)**: 단일 서버 파운데이션 모델 플랫폼. immutable RHEL 이미지(image mode), vLLM+LLM compressor, indemnified Granite(Apache-2.0).

## 고객사례 (덱 수록)

- Turkish Airlines(항공·연료효율 0.2%↑), AGESIC(우루과이·PaaS 확장), DenizBank(120+ 데이터과학자, 1주→10분), Telenor AI Factory(노르딕 소버린, 2026-03), Castilla-La Mancha(15분→5초), Hitachi(전사 산업화), Clalit(2주 만에 프로덕션), City of Vienna.

## 메모

- 영업 토킹포인트·고객사례 중심. 기술 깊이는 [[01-Red-Hat-AI-기술개요]], [[03-AI-Inference-기술개요]] 참고.
- "ogx" = Llama Stack 신규 명칭으로 표기됨 (자료 시점 2026-02).
