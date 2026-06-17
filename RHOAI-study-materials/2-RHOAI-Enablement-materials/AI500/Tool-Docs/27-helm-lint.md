# helm lint — 공식 문서

- **링크**: https://helm.sh/docs/helm/helm_lint/
- **분류**: Tool-Docs / DevOps
- **한 줄**: Helm 차트가 올바른 형식인지 일련의 테스트로 검증하는 명령.

## 목적

"takes a path to a chart and runs a series of tests to verify that the chart is well-formed." 배포 전 차트 문제를 잡는 QA 도구.

## 심각도

- **[ERROR]** — 설치를 막는 문제
- **[WARNING]** — 컨벤션 위반/권고 (배포는 가능)

## 주요 옵션

- `--kube-version` — K8s 버전별 기능·deprecation 체크
- `--strict` — 경고를 실패로 승격
- `--with-subcharts` — 의존 차트까지 검증
- `--set`/`--values` — 린팅 시 동적 값 주입
- `--skip-schema-validation`, `--quiet`

## 워크숍 맥락

Helm 차트 개발의 1차 검증. [26-kubelinter](26-kubelinter.md)(보안·운영 정책)와 상보적. [21-argocd](21-argocd.md)가 Helm 차트를 배포하므로 사전 린트로 안정성 확보.
