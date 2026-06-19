# 매니페스트 (Day별 YAML)

> 기준: OCP 4.21 / RHOAI 3.3 / KServe **Serverless(Knative)** / AI500 환경(설치 전제).
> 네임스페이스(DS Project) = `ai-enablement`(멀티모델은 `ai-multimodel`). 적용 전 이미지·도메인 조정.

| 파일 | 내용 | 환경 |
|---|---|---|
| `day01-kserve-serving.yaml` | 데이터커넥션 + sklearn ServingRuntime + ISVC(Serverless) | A(CPU) |
| `day02-multiframework.yaml` | TF + PyTorch(ONNX/OVMS) ISVC | A |
| `day03-canary-bluegreen.yaml` | **카나리(`canaryTrafficPercent`)** + Blue-Green | A |
| `day04-custom-modelmesh.yaml` | 커스텀 Runtime + **ModelMesh 멀티모델** | A |
| `day05-onboarding.md` | 고객 모델 온보딩 통합 + 성능 | A |
| `day06-workbench.yaml` | Workbench(Notebook) + Git | A |
| `day07-dspa.yaml` + `day07-pipeline.py` | KFP 백엔드 + 3단계 파이프라인 | A |
| `day08-model-registry.yaml` | Registry→KServe 연동 | A |
| `day09-rbac-secret.yaml` | RBAC + Secret + PVC | A |
| `day10-e2e.md` | E2E + Week2 정리 | A |
| `day11-kueue-gpu.yaml` | GPU 노드 + Kueue + 우선순위 | B(GPU) |
| `day12-gpu-sharing.yaml` | Time-Slicing + MIG + HardwareProfile | B |
| `day13-monitoring-ratelimit.yaml` | Prometheus/Grafana + Rate Limiting | B |
| `day14-maas-llmd.yaml` | vLLM + llm-d(LLMInferenceService) | B |
| `day15-integration-runbook.md` | 통합 + 장애 + 고객 시나리오 | 공통 |

## 핵심 — v0.9 환경(Serverless) 고유점

- **`serving.kserve.io/deploymentMode: Serverless`**: 모든 ISVC에 명시(또는 클러스터 기본).
- **카나리**: `spec.predictor.canaryTrafficPercent`는 **Serverless 전용** — RawDeployment엔 없음.
- **ModelMesh**: `modelmesh-enabled: "true"` 라벨 + `multiModel: true` 런타임. (3.4부터 deprecated)
- **설치 트랙 없음**: 클러스터·RHOAI가 이미 깔린 전제(AI500). 빈 클러스터부터 만드는 버전은 v1.0 자료 참조.

## 공통 주의

- 이미지(`quay.io/modh/...`)·llm-d API group은 예시 — 클러스터 설치본·`oc explain`으로 확인.
- 적용 순서: day01→02→03→04 (서빙) → 06→07→08→09 (ML·보안) → 11~14 (GPU, Env B).
