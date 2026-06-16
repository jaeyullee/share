# Flake8 — 공식 문서

- **링크**: https://flake8.pycqa.org/en/latest/
- **분류**: Tool-Docs / DevOps
- **한 줄**: Python 스타일 가이드 준수를 강제하는 린터 (pyflakes + pycodestyle + mccabe 래핑).

## 무엇인가

"Your Tool For Style Guide Enforcement." 포맷팅·공백·코드 복잡도 등 다차원 스타일을 위반 코드(E123, W503, E203 등)로 검사하는 CLI 린터.

## 사용법

```
python -m pip install flake8
flake8 path/to/code/to/check.py
```

## 설정

- `--select` — 특정 검사만 타깃
- `--extend-ignore` — 특정 에러 코드 무시
- 설정 파일로 상세 구성
- **주의**: 실행 Python 버전에 종속 → 대상 버전에 맞춰 설치

## 워크숍 맥락

[[24-black]](포맷)이 모양을 잡고, Flake8은 잠재 버그·복잡도·스타일 위반을 잡음. [[../References/06-made-with-ml]] "Utilities" + [[22-tekton]] CI 린팅 스텝.
