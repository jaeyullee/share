---
title: Red Hat OpenShift AI (production AI for cloud) 데이터시트 (링크) 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - rhoai
  - openshift
  - datasheet
source: https://www.redhat.com/en/resources/production-ai-for-cloud-environments-datasheet
---

# Red Hat OpenShift AI 데이터시트 정리 (링크)

> 원본 링크: https://www.redhat.com/en/resources/production-ai-for-cloud-environments-datasheet
> (reference_link.md 2번째 링크. WebFetch 요약 — 게이트형 데이터시트일 수 있어 핵심만.)
> 상위 맥락: [[00-인덱스]] / 포트폴리오 맥락 [[07-프로덕션-운영-엔터프라이즈플랫폼]]

---

## 제품 개요

**Red Hat OpenShift AI (RHOAI)** — 전통(예측)·에이전트·생성 AI 모델을 프라이빗/하이브리드 클라우드 전반에서 개발·학습·배포하는 종합 플랫폼. Red Hat AI의 핵심 컴포넌트. 대상: IT 운영, 플랫폼 엔지니어, 데이터 과학자, AI 엔지니어.

## 주요 기능

- **모델 개발** — 큐레이트 AI/ML 라이브러리 사전탑재 셀프서비스 노트북·IDE.
- **모델 학습** — GPU 클러스터 분산 워크로드, 실험 추적, 버전 아티팩트.
- **지능형 HW 할당** — 스마트 GPU 스케줄링, 쿼터, 우선순위 기반 접근.
- **AI 파이프라인** — 자동·버전화 워크플로(수동 핸드오프 제거).
- **모델 서빙** — **vLLM** 기반 프로덕션 LLM 서빙 + 예측 ML 배포.
- **에이전트 AI** — Agent Ops, 통합 API 레이어, **MLflow** 추적성.
- **모델 관찰성** — 실시간 성능 모니터, 데이터 drift 탐지, bias 추적.
- **Evaluation Hub** — 모델·RAG·에이전트 과학적 벤치마킹.
- **Catalog & Registry** — AI 자산(모델·메타데이터) 중앙 거버넌스.
- **Feature Store** — 재사용 피처 정의 중앙화.
- **AI 안전** — jailbreak·프롬프트 인젝션·toxic 출력 등 공격 탐지(자동 스캔).
- **엣지 배포** — disconnected·air-gapped 지원.

## 인프라 / 파트너

- **HW**: CPU, GPU(NVIDIA·AMD), XPU(Intel). 온프렘·소버린·퍼블릭 클라우드 지능형 할당.
- **파트너**: Starburst(분산 데이터), HPE(데이터 lineage·버전), NVIDIA·AMD·Intel(GPU·성능), Elastic·EDB(RAG 벡터DB).

## 혜택 / 유스케이스

- AI 도입 단순화·운영 복잡성↓, 협업팀 운영 일관성, any HW 스케일 유연성, 데이터 주권·거버넌스.
- 유스케이스: 사내 데이터로 gen AI 파운데이션 모델 커스터마이징 / 프로덕션 스케일 예측·생성 AI / 멀티클러스터 분산 워크로드 / 하이브리드 이식성.

## 메모

- RHOAI 제품 상세는 [[07-프로덕션-운영-엔터프라이즈플랫폼]] §OpenShift AI, [[02-Red-Hat-AI-플랫폼-고객덱]] 제품 슬라이드 참고.
- 관련 vault: [[02-OpenShift-AI-플랫폼-아키텍처]], [[03-rhoai-mlops-knowledge]], [[project_rhoai_tracker]] (기능 라이프사이클 추적).
- 링크 본문이 폼 게이트일 경우 위 요약은 공개 메타데이터 기준.
