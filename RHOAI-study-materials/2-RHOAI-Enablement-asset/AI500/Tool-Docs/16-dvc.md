# DVC (Data Version Control) — 공식 문서

- **링크**: https://dvc.org/doc
- **분류**: Tool-Docs / AI
- **한 줄**: Git 위에서 대용량 데이터·모델·ML 파이프라인을 버전 관리하는 시스템.

## 핵심 기능

- **데이터·모델 버전 관리** — Git이 못 다루는 대용량 파일 추적
- **파이프라인 관리** — 재현 가능한 데이터 처리·ML 워크플로 정의·실행
- **실험 추적** — 파라미터별 실험 실행·비교·시각화
- **Model Registry** — 학습 모델 버전 조직·관리

## Git과의 동작

메타데이터 파일(`.dvc`, `dvc.yaml`)은 Git 레포에 저장하고, 실제 데이터는 원격 스토리지(S3, Azure, GCS 등)에 보관하는 하이브리드 방식. 코드·데이터·모델을 함께 버전 관리하면서 스토리지 효율 유지.

## 문서 범위

플랫폼별 설치, 시작 가이드, 프로젝트 구조·데이터 관리 user 가이드, 명령 레퍼런스, Python API, 실험 로깅용 DVCLive, PyTorch·TensorFlow 연동.

## 워크숍 맥락

MLOps 재현성(reproducibility) 축의 핵심 도구. [[../References/07-google-mlops]]의 데이터/모델 버전 관리, [[../References/06-made-with-ml]]의 "Reproducibility" 섹션과 직결.
