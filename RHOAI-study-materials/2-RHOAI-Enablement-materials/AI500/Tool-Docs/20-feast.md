# Feast — 공식 문서

- **링크**: https://docs.feast.dev/
- **분류**: Tool-Docs / AI
- **한 줄**: 학습·서빙용 피처를 정의·관리·검증·제공하는 오픈소스 Feature Store.

## 무엇인가

"define, manage, validate, and serve features for production AI/ML." 두 인프라 레이어로 동작 — 학습용 히스토리 추출의 **offline store**, 저지연 프로덕션 서빙의 **online store**.

## 핵심 구성요소

- **Offline Store** — 배치 스코어링·모델 학습용 히스토리 데이터
- **Online Store** — 실시간 예측, 저지연 피처 조회
- **Feature Server** — 비Python 앱의 피처 접근(옵션)
- **Python SDK** — 피처·엔티티·데이터소스 정의

## 핵심 원리

online 서빙에 **push 모델** 사용(요청 대기 대신 값을 능동적으로 push) → 지연 감소. 스토리지와 조회를 분리하는 통합 데이터 액세스 레이어로 모델 이식성 확보, **point-in-time-correct** 피처셋으로 데이터 누수 방지.

## 문서 범위

quickstart, 개념·아키텍처, 튜토리얼, 플랫폼별 가이드(Snowflake/GCP/AWS), API 레퍼런스.

## 워크숍 맥락

[../References/07-google-mlops](../References/07-google-mlops.md) Level 1의 "Feature Store"를 구현하는 도구. 용어집의 Feature Store·Feature Engineering과 직결.
