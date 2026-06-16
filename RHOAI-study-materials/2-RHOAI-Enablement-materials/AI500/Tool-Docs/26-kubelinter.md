# KubeLinter — 공식 문서

- **링크**: https://docs.kubelinter.io/
- **분류**: Tool-Docs / DevOps
- **한 줄**: Kubernetes YAML·Helm 차트를 배포 전에 정적 분석하는 린터 (StackRox/Red Hat).

## 무엇인가

K8s 매니페스트·Helm 차트를 보안 표준·프로덕션 준비도 베스트 프랙티스에 비춰 검사하는 정적 분석 도구. 배포 전에 문제를 잡아주는 "K8s용 코드 린터".

## 검사 내용

- 보안 모범 사례 (예: non-root 실행, 권한 설정)
- 프로덕션 준비도 (리소스 요청/제한, 헬스 프로브, 레이블 등)
- 커뮤니티 가이드라인 준수

## 사용 방식

매니페스트 파일에 대해 실행하는 린팅 워크플로로 통합. **shift-left 보안** — 런타임/프로덕션이 아닌 개발 단계에서 문제 식별.

## 워크숍 맥락

[[27-helm-lint]]가 차트 문법을, KubeLinter는 보안·운영 정책을 검사. [[22-tekton]] CI 또는 [[21-argocd]] 배포 전 게이트. [[../References/02-ai-on-openshift-gitops]]의 RHOAI CR 매니페스트 검증에 활용.
