# 요약 ② MLOps 방법론·실전

> References 중 **MLOps 개념·성숙도·실전 구현·프로젝트 구조** 자료 3종 요약. 상세는 각 개별 노트 참조.
> 묶음: [References/07-google-mlops](References/07-google-mlops.md) · [References/06-made-with-ml](References/06-made-with-ml.md) · [References/08-cookiecutter-data-science](References/08-cookiecutter-data-science.md)

## 개념(왜·무엇) → 실전(어떻게) → 구조(어디에) 순으로 본다.

## 1. 개념·성숙도 — Google MLOps

DevOps 원칙을 ML에 적용한 **성숙도 3단계**:

- **Level 0 (수동)**: 모든 단계 수동, 연 수회 배포, 모니터링 최소 → 모델 성능 저하 방치.
- **Level 1 (파이프라인 자동화)**: 신선한 데이터로 **지속 학습(CT)**. 데이터/모델 검증, **Feature Store**, Metadata Store 도입.
- **Level 2 (CI/CD 자동화)**: 파이프라인 변경을 빠르게 테스트·배포. 6단계(개발→CI→CD→트리거→모델 CD→모니터링).

핵심 개념: **CI**(코드+데이터+모델 검증), **CD**(ML 시스템 전체 배포), **CT**(자동 재학습). "ML 코드는 실제 시스템의 작은 일부일 뿐."

## 2. 실전 구현 — Made With ML

- Anyscale의 교육 플랫폼. **프로덕션 ML 앱을 코드로 설계·개발·배포·반복**.
- 8개 섹션: Design / Data / Model / Development / Utilities / Testing / Reproducibility / Production.
- first-principles 이해 + SW 엔지니어링 베스트 프랙티스 + 확장 가능 Python 워크플로.
- Google MLOps가 "개념/성숙도"라면 Made With ML은 그것을 **실제 구현하는 커리큘럼**.

## 3. 프로젝트 구조 — Cookiecutter Data Science (CCDS)

- DS 프로젝트의 **표준 디렉토리 구조 템플릿**. `ccds` 명령으로 생성.
- 구조: `data/`(raw·interim·processed) · `notebooks/` · `models/` · `reports/` · `references/` · 소스 모듈.
- Made With ML의 "Design/프로젝트 구조"를 실천하는 도구.

## 한 줄 정리

**왜·무엇(Google MLOps 성숙도) → 어떻게(Made With ML 실전) → 어디에(CCDS 구조)**. RHOAI MLOps 파이프라인을 어느 성숙도로 설계할지 판단하는 개념·실천 토대.
