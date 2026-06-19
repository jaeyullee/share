# aboutHandsOn — RHOAI HandsOn 커리큘럼(v0.9) 실습 자료

> RHOAI 컨설턴트 HandsOn 커리큘럼 **v0.9** 기준 enablement 자료(모델·데이터셋·YAML).
> 대상 환경: **주어진 클러스터**(AI500 / Red Hat Demo) — **OCP 4.21 / RHOAI 3.3 / KServe Serverless(Knative)**.
> v0.9는 클러스터가 이미 설치된 전제(설치 트랙 없음) → Day 1부터 모델 서빙으로 시작한다.

## 환경 전제 (v0.9 = AI500 환경)

- **서빙 모드**: KServe **Serverless(Knative)** — Service Mesh/Serverless 오퍼레이터가 깔린 환경.
  → 카나리(`canaryTrafficPercent`)·ModelMesh 등 v0.9 고유 기능을 그대로 사용.
- **Environment A (CPU)**: Day 1-10 (서빙·ML·보안)
- **Environment B (GPU)**: Day 11-15 (GPU 스케줄링·모니터링·MaaS·llm-d)
- 클러스터 접속 정보는 각자 환경에 따름(이 공개 자료엔 포함하지 않음).

## 구성

```
aboutHandsOn/
├── datasets/   # iris, fraud(사기탐지/신용평가), guardrails 샘플 + 생성 스크립트
├── models/     # 모델 학습·변환 스크립트(워크벤치 실행) + LLM HF 링크
└── manifests/  # Day별 YAML (Serverless 기준)
```

## Day ↔ 자료 매핑

| Day | 세션 | 매니페스트 | 모델/데이터 |
|---|---|---|---|
| 1 | KServe 기본 배포 + 트러블슈팅 | `day01-kserve-serving.yaml` | iris `.joblib` |
| 2 | TensorFlow / PyTorch 배포 | `day02-multiframework.yaml` | TF SavedModel, MNIST ONNX |
| 3 | 카나리(`canaryTrafficPercent`) + Blue-Green | `day03-canary-bluegreen.yaml` | fraud v1/v2 |
| 4 | 커스텀 Runtime + 멀티모델(ModelMesh) | `day04-custom-modelmesh.yaml` | 예시 ONNX 2종 |
| 5 | 고객 모델 온보딩 통합 | `day05-onboarding.md` | 전체 |
| 6 | Jupyter Workbench + Git | `day06-workbench.yaml` | iris RandomForest |
| 7 | KFP 파이프라인 + 재사용 | `day07-dspa.yaml` `day07-pipeline.py` | fraud_sample.csv |
| 8 | Model Registry 등록/승격 | `day08-model-registry.yaml` | 등록 모델 |
| 9 | RBAC + Secret 보안 | `day09-rbac-secret.yaml` | — |
| 10 | E2E 훈련→등록→배포 | `day10-e2e.md` | 전체 |
| 11 | GPU 노드 + Kueue + 우선순위 | `day11-kueue-gpu.yaml` | — |
| 12 | GPU 공유(Time-Slicing + MIG) | `day12-gpu-sharing.yaml` | — |
| 13 | Prometheus/Grafana + Rate Limiting | `day13-monitoring-ratelimit.yaml` | — |
| 14 | MaaS(vLLM) + llm-d 벤치마크 | `day14-maas-llmd.yaml` | HF 링크(`models/llm-serving-models.md`) |
| 15 | 통합 + 장애대응 + 고객 시나리오 | `day15-integration-runbook.md` | 전체 |

## v0.9 vs v1.0 (환경 차이 — 헷갈리지 않게)

| 항목 | **v0.9 (이 폴더 / AI500 환경)** | v1.0 (홈 SNO) |
|---|---|---|
| 클러스터 | 주어진 환경(설치 없음) | 빈 SNO 직접 설치 |
| RHOAI | 3.3 | 3.4 |
| 서빙 | **Serverless(Knative)** | RawDeployment |
| 카나리 | **`canaryTrafficPercent`** | Gateway API |
| 멀티모델 | **ModelMesh** | 제외(deprecated) |

## 주의

- 컨테이너 이미지·API 버전은 예시 — 적용 전 클러스터 OOTB 템플릿(`oc get template -n redhat-ods-applications`)·`oc explain`으로 대조.
- 시나리오의 고객 명칭은 일반화(금융/제조/보안). 특정 고객·인프라 접속 정보는 포함하지 않는다.
