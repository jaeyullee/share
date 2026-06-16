---
title: Get started with AI for enterprise organizations (beginner's guide) 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - beginner
  - roadmap
  - sovereign
source: Get started with AI for enterprise organizations_ A beginner's guide.PDF
---

# Get started with AI for enterprise organizations — A beginner's guide 정리

> 원본: `Get started with AI for enterprise organizations_ A beginner's guide.PDF` — 기업 AI 도입 입문서. 용어·모델선택·9단계 로드맵.
> 상위 맥락: [[00-인덱스]]

---

## 1. 용어 (Ch. 도입)

- **Foundation model** — 광범위 데이터로 학습된 범용 베이스(파인튜닝해 도메인 태스크).
- **Frontier model** — 시점별 최강 모델(상대적 용어).
- **Gen AI** — 기존 데이터 학습 후 새 콘텐츠 생성.
- **LLM** — 대량 텍스트 학습 파운데이션 모델.
- **SLM (Small Language Model)** — 1~10B 컴팩트·효율, 특정 유스케이스 최적.
- **AI 종류**: Predictive AI(패턴·예측) / Gen AI(콘텐츠 생성) / Computer Vision(객체탐지·분류).

## 2. AI의 부상 (Ch.1)

- 2017 Google "Attention Is All You Need" → **transformer** → 오늘날 LLM 기반.
- **추론(reasoning) 모델 2025년 등장** — RL 기반 chain-of-thought·자기검증·오류수정 → 에이전트 워크플로 토대.
- **멀티모델 접근** — 복잡 작업은 대형 추론모델(쿼리 5~10%), 단순은 7~13B로 라우팅 → 비용 절감.
- **토큰 = AI의 통화** — 백만 토큰당 과금. 예: 단순쿼리 80%를 소형 모델로.
- **Llama Stack** = "AI 에이전트용 Kubernetes" (추론·RAG·에이전트·툴·안전 공통 API).

## 3. 올바른 모델 선택 (Ch.2)

- 한 앱이 여러 AI 사용(예측+생성+이미지인식). 최신 릴리스 쫓지 말고 **유스케이스에 맞춤**.
- 파운데이션 모델 = 유연하나 자원·비용·복잡성↑. **SLM = 중간점**(2B~70B+, 적은 자원, 많은 경우 동등 성능).
- 원칙: **"정확도 요건을 충족하는 가장 작은 모델"**.

### 모델 구축 vs 튜닝
- 처음부터 구축 = 데이터·컴퓨트·전문성 큼. 대안 = **fine-tuning(transfer learning)**.
- **커스터마이징 기법**:
  - **RAG** — 쿼리 시 외부 지식(벡터DB) 연결. 최신 정보·자주 변하는 정보.
  - **Fine-tuning** — 모델 행동·추론·응답 변경. (RAG와 다른 문제 해결, 둘 병용 흔함.)
  - **RAFT** — RAG 시나리오 모방 학습(관련/무관 컨텍스트 Q&A), 검색 컨텍스트 활용력↑.
  - **Agentic AI** — 모델을 기업 시스템에 연결(DB·API·액션).
  - **Prompt engineering** — few/zero/many-shot, 시스템 프롬프트.
- 실전은 계층화: 파인튜닝 SLM + RAG + 에이전트 프레임워크 + 프롬프트.

### 하드웨어
- **CPU**(범용) / **GPU**(병렬·딥러닝 학습) / **TPU**(ML 텐서연산) / **NPU**(신규 AI 효율).

### 소버린 AI
- 데이터·모델·추론을 통제권 내(온프렘/특정지역/신뢰 클라우드)에.
- 동인: 규제(**EU AI Act 2025 발효**, GDPR, HIPAA), 데이터 거주성, 비용 예측성, 벤더 독립, 성능(엣지 저지연).
- **SLM이 소버린 AI를 실용화**(Granite, Mistral, Llama). Gartner: **2027년까지 소형 태스크모델이 범용 LLM보다 3배** 사용.

## 4. 시작 준비 + 9단계 로드맵 (Ch.3)

### 준비도 평가
- 전략 정렬 / 인프라 용량 / 스킬·전문성 / 데이터 성숙도.
- 팀(크로스펑셔널): 비즈니스 이해관계자 · 데이터 엔지니어 · AI/ML 실무자 · IT 운영 · 윤리·컴플라이언스.

### 9단계
1. 문제·성공기준 정의(기술 아닌 비즈니스 문제) → 2. 팀 구성 → 3. 데이터 평가 → 4. 모델 선택(**gen AI studio** 플레이그라운드로 가속) → 5. 데이터 연결(**RAG**, **Docling** 문서 인제스트) → 6. 필요시 커스터마이즈(fine-tuning, SDG, RAFT) → 7. 프로덕션 최적화(양자화: **8-bit ≈1.8x·정확도 완전유지, 4-bit ≈2.4x**; vLLM 추론서버; 분산추론) → 8. guardrails·모니터링(콘텐츠필터·drift) → 9. 반복·스케일.

## 5. Red Hat으로 도입·스케일 (Ch.4)

- OSS 개발모델 = Red Hat 본연. 사내 혁신 아닌 OSS 프로젝트 기반 → 최신성 + 엔터프라이즈 지원.
- 가치: 효율적 추론(vLLM·LLM Compressor) / 데이터 연결(RAG·Training Hub·인제스트) / 에이전트(Llama Stack·MCP) / 하이브리드 배포 / **indemnified IBM Granite**(24x7 지원).
- 가속기: NVIDIA + AMD GPU + Intel Gaudi + IBM Spyre + Google TPU.

## 메모

- **AI 도입 입문 + 소버린 AI** 설명이 명확. SLM·RAFT·멀티모델 라우팅 등 실무 개념 정리에 유용.
- 관련 vault: [[01-RHOAI-기초-용어정리]], [[01-RAG-아키텍처-핵심정리]], [[02-AI-에이전트-도구호출-프롬프트패턴]].
