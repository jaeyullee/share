# Kubeflow Pipelines SDK (kfp) — 공식 문서

- **링크**: https://kubeflow-pipelines.readthedocs.io/en/sdk-2.12.0/
- **분류**: Tool-Docs / AI
- **한 줄**: Python으로 KFP 파이프라인을 작성·컴파일·실행하는 SDK.

## 무엇인가

"Docker 컨테이너 기반의 이식성 있고 확장 가능한 ML 워크플로를 빌드·배포하는 플랫폼." Python 코드/YAML로 다단계 ML 워크플로를 컨테이너 작업 그래프로 구성.

## 핵심 모듈/API

- **dsl** — `@dsl.component`, `@dsl.pipeline` 데코레이터로 컴포넌트·오케스트레이션 정의
- **Client** — `create_run_from_pipeline_func()` 등으로 실행·배포 관리
- **compiler** — Python 파이프라인 정의를 실행 가능 포맷(YAML)으로 컴파일
- **components** — 워크플로 내 개별 컨테이너 작업 캡슐화

## 사용 패턴

타입 어노테이션을 단 Python 함수로 재사용 컴포넌트 정의 → 파이프라인으로 조합 → Client로 클러스터에 제출·실행·모니터링. recurring run, experiment 분류, 아티팩트 저장, 대시보드 시각화 지원.

## 워크숍 맥락

[12-kubeflow-pipelines](12-kubeflow-pipelines.md)를 실제 코드로 다루는 도구. K8s 리소스 제어는 [14-kfp-kubernetes](14-kfp-kubernetes.md) 애드온 필요.
