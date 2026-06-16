# SonarQube Server — 공식 문서

- **링크**: https://docs.sonarsource.com/sonarqube-server/latest/
- **분류**: Tool-Docs / DevOps
- **한 줄**: 코드 품질·보안을 지속 검사하는 정적 분석 플랫폼.

## 무엇인가

SonarQube는 소스코드를 정적 분석해 품질·보안 문제를 지속적으로 점검(continuous code quality & security inspection)하는 서버. CI 파이프라인·IDE와 연동.

## 탐지 항목

- **Bugs** — 잠재적 오류
- **Vulnerabilities / Security Hotspots** — 보안 취약점
- **Code Smells** — 유지보수성 저해 요소
- **Coverage** — 테스트 커버리지
- **Duplications** — 중복 코드

## Quality Gate

머지/릴리스 전 통과해야 하는 품질 기준 집합. 신규 코드의 커버리지·중복·이슈 임계값을 정의해 통과/실패 판정 → CI 게이트로 활용.

## 지원 언어

Java, Python, JavaScript/TypeScript, C/C++, C#, Go 등 다수 언어 지원.

## 워크숍 맥락

[[23-pytest]]·[[24-black]]·[[25-flake8]]이 로컬/파일 단위라면, SonarQube는 프로젝트 전역 품질·보안 게이트. [[22-tekton]] CI에 통합. *(공식 문서 봇 차단 — 확립된 사실 기반 정리)*
