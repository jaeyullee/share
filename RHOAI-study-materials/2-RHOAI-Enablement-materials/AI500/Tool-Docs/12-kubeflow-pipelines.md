# Kubeflow Pipelines (KFP) — 공식 문서

- **링크**: https://www.kubeflow.org/docs/components/pipelines/
- **분류**: Tool-Docs / AI
- **한 줄**: Kubernetes 위에서 컨테이너 기반 ML 워크플로를 오케스트레이션·관리하는 Kubeflow 컴포넌트.

## 핵심 개념

- **Pipeline** — 전체 워크플로 정의
- **Component** — 파이프라인 안에서 실행되는 재사용 작업 단위
- **Run** — 파이프라인의 개별 실행
- **Experiment** — 파이프라인 run들의 모음
- 그 외 Step, Graph, Output Artifact, ML Metadata(계보 추적)

## 아키텍처

Kubernetes-네이티브 리소스 사용. operator 가이드(인스턴스 배포/관리)와 user 가이드(워크플로 구축)로 역할 분리.

## 문서 범위

시작하기 튜토리얼, 컴포넌트 생성(경량 Python / 컨테이너화 / 컨테이너 기반), 데이터·아티팩트 관리, 로컬·클러스터 실행, operator 설정, v2 API 레퍼런스 + 레거시 v1.

## 워크숍 맥락

RHOAI Data Science Pipelines의 기반. [[13-kfp-sdk]]로 파이프라인을 작성하고 [[14-kfp-kubernetes]]로 K8s 기능을 붙임. [[../References/10-redhat-modular-ai-pipelines]]의 재사용 컴포넌트가 여기에 얹힘.
