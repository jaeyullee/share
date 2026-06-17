# Argo CD — 공식 문서

- **링크**: https://argo-cd.readthedocs.io/en/stable/
- **분류**: Tool-Docs / DevOps
- **한 줄**: Git을 단일 진실 소스로 삼는 Kubernetes용 선언적 GitOps 지속 배포(CD) 도구.

## 무엇인가

"a declarative, GitOps continuous delivery tool for Kubernetes." 실행 중 애플리케이션을 감시하며 라이브 상태를 Git의 desired state와 일치시키는 K8s 컨트롤러.

## 핵심 개념

- **GitOps 패턴** — Git 레포가 설정의 단일 진실 소스
- **Sync** — 라이브 환경을 desired state로 자동/수동 동기화
- **Health 모니터링** — 앱 운영 상태 지속 평가
- **Drift 탐지** — desired vs actual 불일치 식별·시각화 (OutOfSync)
- **App of Apps** — ApplicationSet로 계층적 앱 관리

## 문서 범위

배포 전략·sync 옵션·CLI(user), 클러스터·보안·시크릿·재해복구(operator), 통합 빌드·테스트(developer), Helm/Kustomize/Jsonnet·SSO·webhook.

## 워크숍 맥락

[../References/02-ai-on-openshift-gitops](../References/02-ai-on-openshift-gitops.md)에서 RHOAI 리소스를 GitOps로 배포하는 엔진. RHOAI 호환 커스텀 health check 필요.
