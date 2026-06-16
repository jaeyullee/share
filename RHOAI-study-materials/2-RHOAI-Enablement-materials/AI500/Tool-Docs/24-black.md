# Black — 공식 문서

- **링크**: https://black.readthedocs.io/en/stable/
- **분류**: Tool-Docs / DevOps
- **한 줄**: 타협 없는(uncompromising) Python 코드 포매터. 포맷 결정을 도구에 위임.

## 철학

결정론적 포맷팅 + 최소 설정. 어떤 프로젝트에서든 동일한 출력 → 코드 리뷰 diff 최소화. "Black is opinionated so you don't have to be." 스타일 논쟁을 없애고 내용에 집중.

## 특징

- **안전성** — 재포맷 후 원본과 구문적으로 동등함을 검증. stable 상태(향후 큰 스타일 변경 없음)
- **효율** — 스타일 관련 린팅 불평 제거, 생산성 향상
- MIT 라이선스, 에디터·VCS·CI/CD 통합 용이

## 워크숍 맥락

[[../References/06-made-with-ml]]의 "Utilities/styling", pre-commit 워크플로의 자동 포매팅. [[25-flake8]](린팅)과 함께 코드 품질 게이트 구성. [[22-tekton]] CI에서 실행.
