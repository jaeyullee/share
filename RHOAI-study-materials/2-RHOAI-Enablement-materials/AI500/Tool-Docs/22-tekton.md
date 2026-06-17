# Tekton — 공식 문서

- **링크**: https://tekton.dev/
- **분류**: Tool-Docs / DevOps
- **한 줄**: Kubernetes 네이티브 CI/CD 시스템을 구축하는 오픈소스 프레임워크 (CNCF incubating).

## 무엇인가

"a powerful and flexible open-source framework for creating CI/CD systems" — 클라우드·온프레미스에서 빌드·테스트·배포.

## 강점

1. **표준화** — 벤더·언어·환경 전반의 CI/CD 통합 (Jenkins, Jenkins X, Skaffold, Knative 연동)
2. **내장 베스트 프랙티스** — 확장 가능·서버리스·클라우드 네이티브 실행 기본 제공
3. **유연성** — 하부 구현 추상화로 워크플로 커스터마이징

## 핵심 개념 (참고)

Task(작업 단위), Pipeline(Task 조합), TaskRun/PipelineRun(실행 인스턴스), Triggers(이벤트 기반 시작). *(홈페이지에는 개념 상세 미기재 — 일반 지식 보강)*

## 워크숍 맥락

OpenShift Pipelines의 기반. [../References/02-ai-on-openshift-gitops](../References/02-ai-on-openshift-gitops.md)에서 GitOps 미지원인 Data Science Pipelines를 우회 구동하는 데 사용. CI 파이프라인에서 [23-pytest](23-pytest.md)·[24-black](24-black.md)·[26-kubelinter](26-kubelinter.md) 실행.
