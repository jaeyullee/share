# Cookiecutter Data Science (CCDS)

- **링크**: https://cookiecutter-data-science.drivendata.org/
- **분류**: References (학습 자료/도구)
- **한 줄**: 데이터 사이언스 프로젝트를 위한 논리적·표준화된 디렉토리 구조 템플릿 (DrivenData 제작).

## 무엇인가

"a logical, flexible, and reasonably standardized project structure for doing and sharing data science work." 협업·재현성을 높이는 일관된 프로젝트 구조를 제공.

## 생성되는 디렉토리 구조

- **data/** — raw, interim, processed, external 데이터셋
- **notebooks/** — 번호·설명 네이밍의 Jupyter 노트북
- **models/** — 학습된 모델·예측
- **reports/** — 생성된 분석·figure
- **docs/** — 프로젝트 문서(mkdocs)
- **references/** — 데이터 딕셔너리·설명 자료
- **[module_name]/** — 소스코드(config, dataset, feature, modeling, visualization)
- 설정 파일 — README, requirements.txt, Makefile, pyproject.toml, LICENSE

## 사용법

Python 3.9+ 필요. pipx(권장) 또는 pip로 설치 후 `ccds` 명령으로 새 프로젝트 생성. Python 버전·클라우드 스토리지·환경 관리자·테스트 프레임워크·린팅·라이선스 등 옵션 프롬프트.

## 워크숍 맥락

ML 프로젝트를 처음부터 정돈된 구조로 시작하게 해줌. [[06-made-with-ml]]의 "Design/프로젝트 구조" 실천 도구.
