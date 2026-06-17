# Google — MLOps: Continuous delivery and automation pipelines

- **링크**: https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning
- **분류**: References (학습 자료)
- **한 줄**: DevOps 원칙을 ML에 적용한 MLOps 성숙도 3단계(0/1/2)를 정의하는 Google의 대표 아키텍처 문서.

## MLOps Level 0 — 수동 프로세스

- 데이터 분석·준비·학습·검증 **모든 단계 수동**, 스크립트/노트북 기반
- 모델 배포 빈도 낮음(연 수회), 데이터 사이언티스트와 운영팀 분리
- 노트북 실행 외 테스트 없음, 프로덕션 모니터링 최소
- **문제**: 모델이 프로덕션에서 성능 저하되어도 수동 개입 전까지 방치

## MLOps Level 1 — ML 파이프라인 자동화

- 학습 파이프라인 자동화 → **신선한 데이터로 지속 학습(CT)**
- 모듈화·컨테이너화된 재사용 컴포넌트
- 신규 구성요소: **데이터 검증**(스키마·통계적 drift), **모델 검증**(오프라인/온라인), **Feature Store**, **Metadata Store**
- 트리거: 스케줄/온디맨드/이벤트/drift 기반
- **한계**: 파이프라인 구현이 소수일 때 적합, 테스트·배포는 여전히 수동

## MLOps Level 2 — CI/CD 파이프라인 자동화

견고한 CI/CD로 파이프라인 변경을 빠르게 테스트·배포.

**6단계**: ① 개발·실험 → ② 파이프라인 CI(빌드·테스트·패키징) → ③ 파이프라인 CD(환경 배포) → ④ 자동 트리거 → ⑤ 모델 CD(예측 서빙) → ⑥ 모니터링

- **CI**: 피처 엔지니어링 단위 테스트, 모델 수렴 검증, 컴포넌트 통합 테스트, 아티팩트 검증
- **CD**: 인프라 호환성 체크, 예측 API 테스트, 부하 테스트, dev/staging 자동 배포 + prod는 수동 승인

## 핵심 개념

- **CI**: 코드뿐 아니라 데이터 검증·모델 테스트까지 포함 (전통 SW보다 넓음)
- **CD**: 단일 모델이 아니라 ML 시스템 전체를 배포
- **CT (Continuous Training)**: ML 고유 — 신규 데이터/성능 저하 시 자동 재학습·서빙

## 핵심 교훈

ML은 SW와 근본적으로 다름(팀 역량·실험적 개발·데이터 품질 테스트·모델 decay 모니터링). "실제 ML 시스템에서 ML 코드는 작은 일부에 불과" — 설정·데이터 검증·서빙·모니터링 인프라가 대부분. 성숙도는 점진 도입 가능.

## 워크숍 맥락

RHOAI MLOps 파이프라인을 어느 성숙도에 두고 설계할지 판단하는 개념 프레임. [06-made-with-ml](06-made-with-ml.md)의 실전 구현과 짝.
