---
title: Before you build - A look at AI agentic systems with Red Hat AI 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - agentic
  - mcp
  - llamastack
source: Before you build_ A look at AI agentic systems with Red Hat AI.PDF
---

# Before you build — A look at AI agentic systems with Red Hat AI 정리

> 원본: `Before you build_ A look at AI agentic systems with Red Hat AI.PDF` — 에이전트 시스템 아키텍처를 기술적으로 다루는 e-book(MCP·Llama Stack 중심).
> 상위 맥락: [[00-인덱스]] / 경영진 관점은 [[13-에이전트AI-경영진가이드]]

---

## 0. 핵심 메시지

- 에이전트 = 챗봇 프롬프팅이 아니다. 프로덕션 에이전트는 **추론·툴 오케스트레이션·메모리·데이터 보호·행동 거버넌스를 조율하는 통합 아키텍처** 필요.
- Red Hat AI(OpenShift AI + Llama Stack)가 그 **scaffolding** 제공. **MCP** 오픈 표준으로 툴 발견·사용 통일.

## 1. 에이전트 시스템 구성요소

- Tool use / Planning·Execution / Reasoning / Orchestration / Communication protocols.
- 일반 LLM보다 많은 역량. 단발 어시스턴트 아닌 **멀티스텝 워크플로**(추론·메모리 내장, 위임·결정 체크포인트).

### 용어
- **Agentic AI systems** — 여러 AI 시스템이 추론·메모리·계획·외부툴로 복잡 작업 수행.
- **MCP** — 에이전트가 툴·데이터·메모리와 일관·해석가능하게 상호작용하는 오픈 표준.
- **Llama Stack** — Llama 모델을 프로덕션 툴(API·오케스트레이션·로깅·툴 통합)로 감싸는 통합 레이어.
- **LangChain** — OSS 프레임워크. Red Hat AI 기본은 아니나 유연 지원.

## 2. Red Hat AI로 에이전트 구축 (Ch.1)

- 에이전트 핵심 = reason·plan·act·learn. 추론체인(서브태스크 분할)·프롬프트·메모리·외부툴.
- 시작은 관리가능 유스케이스 → 확장. 예: 사내 검색 에이전트, 로그 교정·IT 인시던트(OpenShift 관찰성 + Ansible + API), AI 코드 마이그레이션.
- **유스케이스(실사례)**: 헬스케어 임상시험 모집(SMS/음성, HIPAA 준수, 환자데이터 학습 미사용).

## 3. OpenShift AI — 엔터프라이즈 라이프사이클 플랫폼 (Ch.2)

- 프로토타입→프로덕션 전환이 최대 난제. **operator 기반** 모델(배포 베스트프랙티스 인코딩, autoscaling·관찰성·튜닝·스케일 자동화).
- Llama Stack·MCP 네이티브 통합 → 로컬 테스트 인터페이스를 프로덕션에서 동일 사용. MCP 서버가 툴 노출 표준화.
- 보안·컴플라이언스 내장(guardrails, RBAC), 관찰성으로 에이전트 결정·툴 호출 추적.
- **유스케이스**: 조달 어시스턴트(ERP API via MCP, 정책 해석, 벤더 승인 추천).

## 4. MCP — 에이전트-툴 표준화 (Ch.3)

- LLM은 추론 제공, 툴은 액션·시스템 접근·실시간 정보. MCP = 그 사이 연결조직. 최근 도입됐으나 빠르게 표준화.
- MCP 이전엔 수동·비일관 통합(커스텀 코드, 중복, 리스크). MCP = "AI 워크플로의 USB-C". 모듈·상호운용 스펙으로 발견·선택·호출.
- MCP 서버 = 툴 호스팅·문서화·보안 허브. 에이전트가 동적 질의·추론·호출.
- **위험**: 빈약한 tool description → 오작동·hallucination. 안전하지 않은 prompt string·과도 권한 → 공격 벡터.
- **MCP Gateway 로드맵** — 거버넌스·보안·관찰성을 MCP 서버 아키텍처에 내장. OpenShift AI 배포 시 플랫폼 정책·RBAC·감사 상속. 컨테이너/앱 보안 툴체인으로 tool description·prompt schema 취약점 스캔.
- **유스케이스**: 사이버보안사 고객지원(intake→classification(감성·긴급·욕설)→resolution(RAG)→routing(에스컬레이션), human validation, Airtable 로그).

## 5. Llama Stack — 통합 AI API 서버 (Ch.4)

- Red Hat의 통합 AI 컨트롤 플레인. **OpenAI 호환 API 서버**(추론·메모리·툴 오케스트레이션·평가).
- 대부분 호스티드 서비스와 달리 **자체 HW/클러스터에서 호스티드형 경험** → 데이터 주권·인프라 요건·벤더 비종속.
- 풀 에이전트 라이프사이클 표준 API(추론 넘어 RAG·safety·eval·telemetry·context-aware). 로컬 경량→엔터프라이즈 동일 API.
- 도입 방식: 빌트인 클라이언트·SDK(tool calling·메모리·컨텍스트) / OpenAI tool-use 호환 / 기존 에이전트·워크플로 재아키텍처 없이 통합.
- OpenShift AI 내 **Kubernetes Operator**가 라이프사이클(autoscaling·관찰성·접근통제). **OpenTelemetry** 네이티브, **TrustyAI** 안전툴 표준화, MCP 서버 연동.
- 모듈 구성: Datasets/Inference/Vector.io/Telemetry/Agentic/Evaluation/Safety/Tool calling(MCP). Red Hat AI는 ① Llama Stack 네이티브 빌드 ② 호환 구현 가져오기 ③ 자체 프레임워크 + 선택적 Llama Stack API ④ Core Primitives.
- **유스케이스**: 개발자 생산성(Java 코드 마이그레이션 어시스턴트, Llama Stack 추론 + MCP 툴 호환성 검증).

## 6. 결론

- 표준화 없으면 단편화·비효율·운영 리스크. OpenShift AI + MCP + Llama Stack으로 PoC→프로덕션.
- 개발자(프로덕션 API), 플랫폼팀(라이프사이클·보안), 조직(오픈 표준으로 투자 보호).

## 메모

- 12는 **에이전트 기술 아키텍처**(MCP·Llama Stack 깊이)가 핵심. 13은 같은 주제 경영진 버전.
- 관련 vault: [[02-AI-에이전트-도구호출-프롬프트패턴]], [[AI-에이전트-환경-구축기]].
