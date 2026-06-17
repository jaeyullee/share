# pytest — 공식 문서

- **링크**: https://docs.pytest.org/en/stable/
- **분류**: Tool-Docs / DevOps
- **한 줄**: 작고 읽기 쉬운 테스트부터 복잡한 기능 테스트까지 확장되는 Python 테스트 프레임워크.

## 핵심 기능

- **Assert introspection** — 평범한 `assert` 문에 대해 실패 원인을 상세 출력 (특수 메서드 불필요)
- **Auto-discovery** — 테스트 모듈·함수 자동 수집
- **Fixtures** — 모듈형·파라미터화 가능한 테스트 리소스 셋업/티어다운
- **Markers & Parametrize** — 커스텀 속성 표시, 동일 테스트를 다양한 입력으로 반복
- **호환성** — unittest 스위트 그대로 실행, Python 3.10+/PyPy3
- **플러그인** — 1,300+ 외부 플러그인 생태계

## 동작

테스트는 단순 함수 + `assert` 문으로 작성. 실행 시 자동 수집·실행하고 무엇이 왜 틀렸는지 상세 출력.

## 워크숍 맥락

[../References/06-made-with-ml](../References/06-made-with-ml.md)의 "Testing"(코드·데이터·모델 검증), [../References/07-google-mlops](../References/07-google-mlops.md) Level 2 CI의 단위 테스트를 구현. [22-tekton](22-tekton.md) 파이프라인의 테스트 스텝.
