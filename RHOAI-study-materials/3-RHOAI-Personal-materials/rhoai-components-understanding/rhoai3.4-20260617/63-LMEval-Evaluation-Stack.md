# LMEval / Evaluation Stack

> 모델 평가 — lm-evaluation-harness 기반 LMEvalJob(성숙) + EvalHub 기반 Evaluation Stack control plane(DP).
> 영역: [60-GenAI평가안전-관계](60-GenAI평가안전-관계.md)

---

## 1. 정의 / 역할
- lm-evaluation-harness(EleutherAI, ~167 벤치마크) + Unitxt(IBM, card/template/task/metric) 기반 평가 서비스.
- `trustyai-service-operator`의 **LMEval controller**가 `LMEvalJob` 처리. → [62-TrustyAI](62-TrustyAI.md)

## 2. 버전 / 라이프사이클
- LMEval(lm-evaluation-harness 0.4.8) **GA급**(별도 라벨 없음).
- Evaluation Stack control plane = **DP**, EvalHub SDK/CLI·LM-Eval UI = **TP**, Garak/RAGAS/GuideLLM = **TP**.

## 3. CRD: LMEvalJob

| 항목 | 값 |
|---|---|
| group/version | `trustyai.opendatahub.io/v1alpha1` |
| kind / scope | `LMEvalJob` / Namespaced |

- spec: `model`(hf / openai-completions / openai-chat-completions / **local-completions** / local-chat-completions), `modelArgs`(model/base_url/tokenizer), `taskList.taskNames`(mmlu 등)/`taskRecipes`(Unitxt)/`custom`, `limit`, `batchSize`(숫자만, `auto:N` 미지원), `allowOnline`, `allowCodeExecution`, `offline`(PVC/S3 air-gap), `outputs`(pvcManaged/oci), `logSamples`.
- status: `state`(New/Scheduled/Running/Complete/Cancelled), `results`(JSON), `podName`.

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata: { name: evaljob }
spec:
  model: local-completions
  modelArgs:
    - { name: model, value: granite }
    - { name: base_url, value: $ROUTE/v1/completions }
  taskList: { taskNames: [mmlu] }
  batchSize: '1'
  logSamples: true
```

## 4. 동작 end-to-end
CR 생성 → controller가 Job/Pod 생성(이미지 `quay.io/trustyai/ta-lmes-job`, GPU 자동감지) → lm-eval-harness 실행 → results.json → `.status.results`. controller 10s 폴링. 전역 ConfigMap `trustyai-service-operator-config`(lmes-default-batch-size=8, lmes-max-batch-size=24).

## 5. Evaluation Stack / EvalHub
- **Evaluation Stack control plane(DP)**: EvalHub 기반 2계층(operator가 `EvalHub` CR 관리, EvalHub Server=Go REST 오케스트레이션). 지원: LM Eval Harness, Garak, GuideLLM, LightEval, RAGAS, MTEB.
- **EvalHub(TP)**: SDK(`eval-hub-sdk`)/CLI(`evalhub eval run`)/`evalhub.mcp`(DP). **MLflow 자동 추적**. Evaluation Collections, Sliced Evaluation.
- **Garak(TP)**: LLM 보안 스캐닝. inline(Llama Stack 내부) vs remote(독립 Job/KFP).

## 6. 연동
- KServe/vLLM 또는 Llama Stack(`remote::lmeval`)을 대상으로 평가 → [61-Llama-Stack](61-Llama-Stack.md).
- 결과 → EvalHub/MLflow.

## 7. 운영 함정
- **보안 2단계 게이트**: `allowOnline`/`allowCodeExecution`는 per-job만으론 부족 — DSC `components.trustyai.eval.lmeval.permitOnline/permitCodeExecution: allow` 선행 필요(기본 deny). Air-gap은 `allowOnline:false` + `offline` PVC.
- Kind는 `LMEvalJob`(`LMEval` 아님). UI는 `OdhDashboardConfig.disableLMEval: false`로 활성.

## 8. 출처
- CRD: https://github.com/trustyai-explainability/trustyai-service-operator (`api/lmes/`, `api/evalhub/`)
- EvalHub: https://developers.redhat.com/articles/2026/05/12/how-evalhub-manages-two-layer-kubernetes-control-planes
- RHOAI 3.4 evaluating_ai_systems
