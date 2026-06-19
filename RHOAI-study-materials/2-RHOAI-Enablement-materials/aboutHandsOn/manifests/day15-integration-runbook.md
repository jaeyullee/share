# Day 15 — 전체 통합 + 장애대응 + 고객 시나리오 모의

> Day 1~14를 한 번에 엮어 E2E를 돌리고, 장애를 주입·복구하고, 고객 시나리오를 모의한다.

## 1. 전체 통합 워크플로우
```
Jupyter 훈련(Day6) → Model Registry 등록(Day8) → KServe 서빙(GPU, Day1~2)
       → Grafana 모니터링(Day13) → LLM 요약(MaaS, Day14) → Rate Limiting(Day13)
```

## 2. 장애 3종 주입 → 복구
| 장애 | 주입 | 진단 | 복구 |
|---|---|---|---|
| 파이프라인 실패 | 잘못된 컬럼/패키지 | Run 로그 / `oc logs <pod>` | 파라미터 수정 → 재실행 |
| InferenceService 장애 | 없는 storageUri / 메모리 과소 | `oc describe isvc`, `oc logs -l serving.kserve.io/inferenceservice=<name>` | 경로/리소스 수정 재적용 |
| GPU 부족 | quota 초과 잡 제출 | `oc describe quota`, Pending 이벤트 | Kueue 큐잉 대기 / 우선순위 조정 |
| 메트릭 이상 | 부하로 P95↑ | Grafana 알림 | replica/리소스 조정 |
| Rate Limit 초과 | 한도 초과 호출 | 429 응답 | 한도 상향 / 백오프 |

## 3. 고객 시나리오 모의 (일반화 — 특정 고객 정보 없음)
| 시나리오 | 모델/데이터 | 핵심 컴포넌트 |
|---|---|---|
| 금융 — 카드 사기탐지 | `fraud_sample.csv` → sklearn/TF | 서빙 + 카나리(Day3) + 모니터링(Day13) + RBAC(Day9) |
| 제조 — 품질 검사(이미지) | (이미지 분류, GPU) | GPU 추론 파이프라인 + 모니터링 + 장애대응 |
| 보안 — 로그 분석 | 분류 모델 + LLM 요약 | 훈련→등록→서빙→모니터링→MaaS 통합 |

## 4. 산출물
- 통합 워크플로우 데모 + 장애 3종 해결 로그 + 아키텍처 문서 + 고객 제안 자료.
