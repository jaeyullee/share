---
title: Red Hat AI Inference 데이터시트 (링크) 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - inference
  - datasheet
source: https://www.redhat.com/en/resources/optimize-ai-inference-datasheet
---

# Red Hat AI Inference 데이터시트 정리 (링크)

> 원본 링크: https://www.redhat.com/en/resources/optimize-ai-inference-datasheet
> (reference_link.md 1번째 링크. WebFetch로 요약 — 본문은 게이트형 데이터시트일 수 있어 핵심만.)
> 상위 맥락: [00-인덱스](00-인덱스.md) / 기술 심화 [03-AI-Inference-기술개요](03-AI-Inference-기술개요.md)

---

## 제품 개요

**Red Hat AI Inference** — 하이브리드 클라우드 전반 AI 모델 배포를 관리하는 추론 최적화 플랫폼. 에이전트 AI 및 내부 **MaaS** 패턴을 운영 통제와 함께 실행.

## 핵심 역량

- Any model · any accelerator (데이터센터·클라우드·엣지)에서 실행.
- 추론 처리 지능형 분산으로 병목 방지.
- 고급 모델 압축 — **양자화 + speculative decoding**.
- Red Hat HF 레포의 프로덕션 준비·검증 오픈 모델.
- **Gen AI 전용 텔레메트리** — TTFT(time-to-first-token), KV-cache 히트율, throughput, GPU 활용률.

## 기술 구성요소

- **vLLM** — 멀티 가속기 고성능 추론 런타임.
- **llm-d** — 가속기 fleet 전반 트래픽 라우팅·밸런싱 분산 추론 엔진.
- **모델 최적화 툴킷** — 정확도 유지하며 HW 요구↓.
- **엔터프라이즈 Kubernetes 배포** — Red Hat OpenShift + 3rd party k8s.

## 혜택

- **토큰 경제** — 프로덕션 용량↑, 토큰당 비용↓.
- **예측가능 스케일** — 에이전트 워크플로의 불규칙 스파이크 대응.
- **하이브리드 유연성** — 온프렘·클라우드·엣지 통합 운영 경험.
- **비용 절감** — 모델 압축으로 HW 요구↓.

## 시작

- 무료 60일 트라이얼 (red.ht/ai-inference-server-trial).
- OpenShift 또는 호환 Kubernetes로 배포.

## 메모

- 데이터시트는 [04-Inference-at-Scale-세일즈](04-Inference-at-Scale-세일즈.md)·[03-AI-Inference-기술개요](03-AI-Inference-기술개요.md) 내용의 1페이지 요약본 성격.
- 링크 본문이 폼 게이트일 경우 위 요약은 공개 메타데이터 기준 — 정확한 수치는 원본 PDF 확인 권장.
