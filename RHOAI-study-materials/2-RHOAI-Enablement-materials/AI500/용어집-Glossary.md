# AI500 — 용어집 (Glossary)

> 출처: [rhoai-mlops lab-instructions — The Reference Track](https://rhoai-mlops.github.io/lab-instructions/#/9-the-reference-track/references)
> 워크숍에서 제공하는 MLOps/ML 용어 정의. References·도구 정리는 [[README]] 참조.

| 용어 | 설명 |
|---|---|
| **MLOps** | AI 모델을 안정적·효율적으로 구축·배포·운영하기 위한 실천 방식, 문화, 도구 |
| **ETL (Extract, Transform, Load)** | 데이터를 수집(extract)·정제/가공(transform)·저장(load)하는 프로세스 |
| **EDA (Exploratory Data Analysis)** | 데이터의 패턴과 문제를 이해하기 위한 탐색적 데이터 분석 |
| **Data Feature** | 모델에 사용되는 개별적이고 측정 가능한 데이터 속성 (예: 나이, 온도, 거래 금액) |
| **Feature Store** | 데이터 피처를 관리하고 제공하는 중앙화 시스템 (→ [[Tool-Docs/20-feast]]) |
| **Feature Engineering** | 모델 성능 향상을 위해 데이터 피처를 생성·수정하는 작업 |
| **Neural Network** | "뉴런" 다층 구조로 만들어진 ML 모델, 높은 복잡도 처리 가능 (→ [[References/04-3blue1brown-neural-networks]]) |
| **Hyperparameter Tuning** | 레이어 수, 학습률 등 모델의 일반 설정을 조정해 성능을 개선하는 것 |
| **Pipeline** | 데이터 처리·학습·배포에 사용하는 자동화된 일련의 단계 |
| **Training** | 데이터를 사용해 ML 모델을 학습시키는 것 |
| **Inference** | 학습된 모델로 예측을 수행하는 것 |
| **Kubeflow** | Kubernetes에서 ML 워크플로를 관리하는 도구 모음 (→ [[Tool-Docs/12-kubeflow-pipelines]]) |
| **Argo CD** | 배포 자동화를 위한 GitOps 도구 (→ [[Tool-Docs/21-argocd]]) |
| **Model Registry** | 모델의 여러 버전을 추적·관리하는 시스템 |
| **Canary Deployment** | 전체 롤아웃 전 소규모 그룹에 새 모델을 먼저 배포 |
| **Shadow Deployment** | 사용자에게 영향을 주지 않고 새 모델을 병렬로 실행 |
| **Data Drift** | 예측 대상 데이터가 학습 데이터와 크게 달라지는 현상 |
| **Bias Detection** | 모델의 불공정하거나 의도치 않은 편향을 식별 (→ [[Tool-Docs/15-trustyai]]) |
| **SHAP (Shapley Additive Explanations)** | 각 피처가 예측에 기여한 정도를 알려줘 모델 예측을 설명하는 방법 |
| **Counterfactuals** | 입력에 다양한 "what-if" 변화를 줘서 원하는 방향으로 출력을 바꿀 수 있는지 검증 |
