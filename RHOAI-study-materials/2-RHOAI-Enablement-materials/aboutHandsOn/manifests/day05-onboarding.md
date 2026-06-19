# Day 5 — 통합 시나리오: 고객 모델 온보딩 + 성능 정리

> 시나리오: 고객이 사기탐지 모델 3개를 OpenShift AI에 배포 요청. Day1~4를 한 번에 엮는다.

## 절차
1. **sklearn 모델 배포(기본)** — `day01-kserve-serving.yaml` (Serverless)
2. **PyTorch 모델 배포(고급)** — `day02-multiframework.yaml`
3. **카나리로 v2 교체** — `day03-canary-bluegreen.yaml` (`canaryTrafficPercent`)
4. **멀티모델 서빙 통합** — `day04-custom-modelmesh.yaml` (ModelMesh)
5. **3개 모델 추론 테스트** — 각 `status.url`에 `curl`

## 성능 테스트(후반 세션)
```bash
# 부하 상황에서 응답시간 측정(간단)
URL=$(oc get isvc fraud-canary -n ai-enablement -o jsonpath='{.status.url}')
time (for i in $(seq 200); do curl -sk $URL/v2/models/fraud-canary/infer -d @../models/fraud/sample_request.json >/dev/null; done)
oc get isvc -n ai-enablement -o wide
```
- 결과를 표로 정리(모델별 p50/p95, replica 수) → 고객 설명 자료.

## 산출물
- 3개 모델 동시 서빙 + 카나리 전환 데모 + 성능표 + 제안 자료.
