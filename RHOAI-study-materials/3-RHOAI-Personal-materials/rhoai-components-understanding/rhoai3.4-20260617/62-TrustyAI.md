# TrustyAI

> 책임있는 AI 툴킷 — 편향/공정성 + 설명가능성 + 드리프트 + LLM 가드레일. 단일 오퍼레이터가 5개 CRD 관리.
> 영역: [60-GenAI평가안전-관계](60-GenAI평가안전-관계.md)

---

## 1. 정의 / 역할
Red Hat·IBM 후원 오픈소스. (1)편향/공정성(SPD, DIR) (2)설명가능성(LIME/SHAP, KServe explainer) (3)드리프트(Meanshift/FourierMMD/KS) (4)가드레일/text safety.

## 2. 버전 / 라이프사이클
- 업스트림 org `trustyai-explainability`, 오퍼레이터 `trustyai-service-operator`(1.37.0).
- 이 **단일 오퍼레이터가 5개 CRD**(group `trustyai.opendatahub.io`): TrustyAIService, GuardrailsOrchestrator, NemoGuardrails, LMEvalJob, EvalHub.

## 3. CRD

### TrustyAIService (v1alpha1 + **v1[storage]**)
- spec(v1): `replicas`, `storage`(format Enum PVC/DATABASE, size, databaseConfigurations), `data`(filename/format), `metrics`(schedule/batchSize).
- ⚠️ 구버전 `predictionLogging`/`payloadProcessor` 필드는 **v1에 없음** — 오래된 매니페스트 그대로 쓰면 안 됨.

### GuardrailsOrchestrator (FMS) — ⚠️ legacy
- `trustyai.opendatahub.io/v1alpha1`. IBM 오픈소스 **fms-guardrails-orchestrator**(Rust) 기반.
- spec: `orchestratorConfig`(ConfigMap), `autoConfig`(`inferenceServiceToGuardrail`로 자동 설정), `enableBuiltInDetectors`(regex 사이드카), `enableGuardrailsGateway`, `otelExporter`.
- orchestratorConfig: `chat_generation.service`(생성 모델=KServe/vLLM) + `detectors`(입출력, `default_threshold`).
- detector: **regex**(email/SSN), **HAP**(hate-abuse-profanity, granite-guardian-hap-38m), 외부 detector(`/api/v1/text/contents`), HuggingFace detector.
- 포트: 8032(chat gen), 8033(LLM predictor), 8080(regex), 4317/4318(OTel).
- ⚠️ **3.4 문서가 FMS Guardrails를 "legacy, deprecate 예정"으로 명시**. (가드레일 기능 전체가 아니라 FMS 오케스트레이터 경로 한정)

### NemoGuardrails — 3.4 주력
- `trustyai.opendatahub.io/v1alpha1`. spec: `nemoConfigs`(ConfigMap 리스트), `caBundleConfig`, `replicas`, `env`. Python/FastAPI, **Colang 프로그래머블**.
- 엔드포인트: `/v1/guardrail/checks`(검증만), `/v1/chat/completions`(가드레일+생성). ⚠️ FMS는 복수형 `/v1/guardrails/checks`.
- Rails: Input/Output/Retrieval. 내장: **Presidio PII**(PERSON/EMAIL/PHONE/CREDIT_CARD/US_SSN/IP), regex, Self-Check(LLM 판정).

(LMEvalJob, EvalHub은 [63-LMEval-Evaluation-Stack](63-LMEval-Evaluation-Stack.md) 참조)

## 4. 동작 / 연동
- **GuardrailsOrchestrator = 모델 앞단 프록시**. `chat_generation`이 KServe predictor 지정, 클라이언트는 orchestrator `/v1/chat/completions` 호출 → 입력 detector → 추론 → 출력 detector. → [31-KServe](31-KServe.md)
- **Llama Stack safety provider**: `remote::trustyai_fms`, `orchestrator_url`이 GuardrailsOrchestrator 지정. Shield 등록(`POST /v1/shields`) → 실행(`POST /v1/safety/run-shield`). → [61-Llama-Stack](61-Llama-Stack.md)
- **TrustyAIService**: KServe payload 수집 → bias/drift/XAI 메트릭 → Prometheus.

## 5. 운영 함정
- **FMS Guardrails = legacy** → 신규는 NeMo 권장. 단 Llama Stack `trustyai_fms` provider는 FMS 의존.
- **TrustyAIService v1alpha1→v1**(v1 storage, 구 필드 제거).
- 엔드포인트 단/복수 표기 차이(NeMo 단수 vs FMS 복수).

## 6. 출처
- 오퍼레이터/CRD: https://github.com/trustyai-explainability/trustyai-service-operator (`api/{tas,gorch,nemo_guardrails,lmes,evalhub}/`)
- 문서: https://trustyai.org/docs/main/main
- RHOAI 3.4 enabling_ai_safety_with_guardrails
