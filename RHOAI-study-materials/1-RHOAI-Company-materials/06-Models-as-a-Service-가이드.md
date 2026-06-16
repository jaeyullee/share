---
title: A guide to Models-as-a-Service 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - maas
  - inference
source: A guide to Models-as-a-Service.PDF
---

# A guide to Models-as-a-Service (MaaS) 정리

> 원본: `A guide to Models-as-a-Service.PDF` — MaaS 개념·운영 모델·Red Hat 내부 구현 가이드.
> 상위 맥락: [[00-인덱스]]

---

## 1. 문제 — "AI 카오스에서 통제로"

- 많은 조직이 OpenAI/Anthropic 등 상용 API로 시작 → 사용 증가 시 비용↑, 데이터 프라이버시·관찰성·커스터마이징 한계, 모델 변경 통보 부족.
- 반대 극단(자체 구축) → 팀별 제각각 Llama/Mistral 배포 → 중복 인프라, 유휴 GPU, 거버넌스·보안 약화, 비용 폭증.
- 최근 LLM(Llama·DeepSeek·Mistral·Qwen)은 **테라바이트급 vRAM** 요구 → 비효율 사용 시 비용 급증.
- 필요: 모델 사용을 **간소화·통합**, HW 자원 최적화, 통제된 확장 접근.

## 2. MaaS 접근

- **MaaS = AI 모델을 공유 자원(API 엔드포인트)으로 제공**. 한 번 배포해 전사 공유.
- 워크플로: Provider(IT/AIOps 팀이 모델 배포·운영) → API Gateway → Consumer(개발자·앱·엔드유저).
- 플랫폼(예: Red Hat OpenShift AI)에 모델 배포 → API 게이트웨이 노출. 사용자는 GPU/TPU 직접 관리 불필요, "모델 접근만 제공하고 자원은 숨김".
- **토큰 레벨(in/out) 추적**이 GPU 메트릭보다 정확.

## 3. 통제·throttle·비용 관리

- IT/플랫폼 엔지니어: 무단 배포 방지, 보안·컴플라이언스, 라이프사이클 단순화.
- 재무팀: 중앙 사용추적·내부 차지백으로 낭비↓, GPU 사용 예측가능.
- **API Gateway가 핵심**: 정밀 사용추적(토큰 단위), 비용 귀속, throttle(자원 독점 방지), 자격증명 관리(생성·취소·수정).

## 4. Any model / accelerator / cloud

- 기존 AI 도입의 경직성(클라우드 종속, 독점 모델 생태계, 고정 HW)을 MaaS가 해소.
- 오픈소스·독점·커스텀·인기 LLM(Llama, Mistral) 지원. 텍스트 외 예측분석·비전·오디오·이미지/비디오 생성.
- 가속기 불가지론(GPU 등 자유 선택). 온프렘·하이브리드·**air-gapped**·퍼블릭 — 규제 산업·데이터 주권에 유용.

## 5. Red Hat 내부 구현

- 사내 AI 팀이 OpenShift + OpenShift AI로 모델 배포·접근 중앙화.
- OpenShift AI 내 GPU 스케일러블 서빙 + 중앙 API 게이트웨이. **토큰 기반 모니터링**으로 누가·얼마나 사용하는지 추적, 비용 귀속.
- **GitOps 워크플로**로 고가용성·신뢰성, 수동개입↓.
- 효과: 중복 제거, 운영 간소화, time-to-value 가속. 검증된 신규 모델 즉시 통합.

## 6. 시작하기

- MaaS 설명서 → OpenShift AI 제품 페이지(GPU 사용 가이드) → **Red Hat Consulting**(모델 서빙 환경 설계·운영화).

## 메모

- MaaS는 거의 모든 자료에 등장하는 핵심 패턴. 기술 구현은 [[01-Red-Hat-AI-기술개요]] §llm-d/MaaS, 영업 수치는 [[04-Inference-at-Scale-세일즈]].
- 인터랙티브 데모: red.ht/maas-pattern.
