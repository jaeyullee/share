# Day 10 — End-to-End: 훈련 → 등록 → 배포 + Week 2 정리

> 시나리오: 신용평가 모델을 처음부터 끝까지. 산출물 = 개인 Cheat Sheet + 트러블슈팅 노트.

## E2E 절차
1. **훈련** — 워크벤치에서 `models/train_fraud_sklearn.py`(또는 RandomForest) → `model.joblib`
2. **등록** — Model Registry v1 등록(`day08-model-registry.yaml` 주석의 SDK 절차)
3. **배포** — `day01-kserve-serving.yaml` 패턴으로 KServe(Serverless) 배포
4. **추론 테스트** — `status.url`에 `curl`
5. **카나리로 v2 전환** — `day03-canary-bluegreen.yaml`의 `canaryTrafficPercent`

## Week 2 정리(문서화)
- 아키텍처 다이어그램(훈련→등록→서빙)
- 주요 명령 Cheat Sheet (`oc get isvc`, `oc describe`, `oc logs -l serving.kserve.io/inferenceservice=<name>`)
- 발생 문제·해결 기록(트러블슈팅 노트)
