# LLM 평가 동향과 RHOAI LMEval 비교

> 2026-07-21 조사 | 커뮤니티·연구 동향 및 Red Hat OpenShift AI 3.5 문서 기준 | 공개 공유용

---

## 1. 한 줄 결론

LLM 평가의 중심은 **고정된 문제집으로 모델 하나의 점수를 재는 일**에서 **실제 애플리케이션·RAG·에이전트가 업무를 안전하고 일관되게 끝내는지 지속 검증하는 일**로 이동하고 있다.

RHOAI의 **LM-Eval**은 이 중 표준 모델 벤치마크를 Kubernetes Job으로 재현 가능하게 실행하는 강한 기반이다. 그러나 커뮤니티가 말하는 넓은 의미의 LLM 평가를 모두 담당하지는 않는다. RHOAI에서는 다음과 같이 역할을 나눠 봐야 정확하다.

```text
모델 능력·정확도      → LM-Eval / LM Evaluation Harness
평가 통합·실험 추적   → EvalHub / MLflow
RAG 품질             → RAGAS
안전·취약점          → Garak / Automated Risk Assessment
서빙 성능            → GuideLLM
에이전트·업무 성공률  → 커스텀 EvalHub provider 또는 별도 실행형 평가
운영 중 품질          → trace 수집 + 온라인/샘플링 평가 + 사람 검토
```

따라서 **“RHOAI LMEval 도입 = LLM 평가 체계 완성”은 아니다.** 올바른 포지셔닝은 **LMEval을 모델 평가 엔진으로 두고, EvalHub를 control plane으로 확장하면서 업무별 gold set·trace·사람 검토를 결합하는 것**이다.

---

## 2. LLM 평가는 무엇을 평가하는가

LLM 평가를 하나의 정확도 점수로 이해하면 범위가 너무 좁다. 현재 실무에서는 최소 다섯 계층을 구분한다.

| 계층 | 핵심 질문 | 대표 지표·방법 | 대표 도구·벤치마크 |
|---|---|---|---|
| 모델 능력 | 모델 자체가 지식·추론·코딩을 얼마나 잘하는가? | accuracy, exact match, pass@k | LM Evaluation Harness, LightEval, MMLU-Pro, GPQA |
| 애플리케이션 품질 | 프롬프트·RAG·라우팅을 포함한 최종 답이 좋은가? | relevance, faithfulness, groundedness, rubric score | RAGAS, DeepEval, Promptfoo, MLflow GenAI eval |
| 에이전트 행동 | 올바른 도구를 쓰고 정책을 지키며 업무를 끝냈는가? | task success, 최종 상태, 잘못된 tool call, pass^k | τ-bench, SWE-bench, Inspect AI, 커스텀 환경 테스트 |
| 안전·보안 | 유해 출력, jailbreak, prompt injection, 데이터 유출을 막는가? | attack success rate, refusal quality, policy violation | Garak, Promptfoo red team, HarmBench 계열 |
| 운영 품질 | 실제 부하와 사용자 분포에서 빠르고 안정적인가? | TTFT, ITL, latency, throughput, cost, 오류율, 품질 회귀 | GuideLLM, trace observability, production sampling |

중요한 변화는 **평가 대상의 단위가 모델에서 시스템으로 커졌다는 점**이다. 같은 모델이라도 system prompt, 검색기, chunking, reranker, tool schema, memory, retry 정책이 달라지면 결과가 크게 달라진다. 모델 leaderboard만으로 실제 서비스 품질을 예측하기 어려운 이유다.

---

## 3. 2025~2026년 커뮤니티·연구 동향

### 3-1. 정적 benchmark에서 live·dynamic·private eval로 이동

MMLU 같은 공개 정적 benchmark는 비교가 쉽지만, 시간이 지날수록 다음 문제가 커진다.

- 모델 학습 데이터에 시험 문제가 들어가는 **data contamination**
- 상위 모델 점수가 비슷해지는 **benchmark saturation**
- 점수는 높지만 실제 업무에서는 실패하는 **현실 대표성 부족**

[LiveBench](https://proceedings.iclr.cc/paper_files/paper/2025/hash/e4a46394ba5378b3f9a186a5b4c650d1-Abstract-Conference.html)는 최근 공개 자료로 문제를 계속 갱신해 contamination을 줄이는 방향을 보여준다. [EMNLP 2025의 contamination 연구](https://aclanthology.org/2025.emnlp-main.511/)는 정적 데이터에 변환 함수를 적용하거나 새 문제를 지속 생성하는 dynamic benchmarking을 별도 연구 영역으로 정리했다.

실무적 결론은 간단하다.

- 공개 benchmark는 **모델의 기초 체력과 회귀 확인**에 쓴다.
- 최종 선정은 조직의 실제 요청을 익명화한 **비공개 domain eval set**으로 한다.
- 운영 실패 사례를 다시 eval set에 넣어 시험 문제를 계속 갱신한다.

### 3-2. LLM-as-a-Judge 확산과 동시에 ‘judge 평가’가 새 문제로 부상

자유 형식 답변은 exact match로 채점하기 어렵다. 이 때문에 LLM이 유용성·정확성·안전성·문체 등을 rubric에 따라 채점하는 **LLM-as-a-Judge**가 빠르게 확산됐다.

장점은 명확하다.

- 사람이 전부 읽는 것보다 빠르고 저렴하다.
- reference answer가 없는 요약·창작·대화 품질도 평가할 수 있다.
- 자연어 rubric으로 업무 기준을 표현할 수 있다.

그러나 judge도 모델이므로 신뢰성 문제가 생긴다. [ICLR 2025 연구](https://proceedings.iclr.cc/paper_files/paper/2025/hash/fdca08d371e4b6c031397909e20043bd-Abstract-Conference.html)는 LLM judge의 여러 체계적 bias를 정량화했고, 최근 연구는 position·verbosity·style·self-preference·prompt sensitivity와 반복 평가 불일치를 계속 다룬다.

따라서 실무 패턴은 **judge 점수 하나를 진실로 취급하는 것**이 아니라 다음 조합으로 이동하고 있다.

1. 가능한 항목은 schema·정규식·DB 최종 상태·코드 테스트 같은 **결정론적 검사**로 먼저 채점한다.
2. 주관적 품질만 명확한 rubric의 LLM judge에 맡긴다.
3. judge 모델·prompt가 바뀌면 사람이 채점한 작은 gold set으로 다시 보정한다.
4. pairwise 비교 시 답변 순서를 바꿔 재평가하고, 불일치 사례를 사람에게 보낸다.
5. 고위험 항목은 표본 human review를 유지한다.

최근 현업 커뮤니티에서도 “judge는 대량 triage와 smoke test에 유용하지만 단일 절대점수로 쓰기에는 불안하다”는 경험이 반복된다. 이는 정량 연구를 대체하는 근거는 아니지만, 연구에서 발견한 bias가 운영에서도 체감되고 있음을 보여주는 신호다. 예: [2026년 6월 r/MLOps 토론](https://www.reddit.com/r/mlops/comments/1uh4b4l/how_are_you_all_actually_evaluating_llmagent/).

### 3-3. 모델 출력보다 agent trajectory와 최종 환경 상태를 평가

에이전트는 자연어 답변만 생성하지 않는다. 여러 차례 tool call을 하고 외부 시스템의 상태를 바꾼다. 이때 최종 답변이 그럴듯한지만 보면 다음 실패를 놓친다.

- 권한 밖의 도구를 호출했다.
- 불필요한 API를 여러 번 호출해 비용과 위험을 키웠다.
- 중간 단계에서 정책을 위반했지만 마지막 답은 맞았다.
- 한 번은 성공하지만 반복 실행 시 성공률이 급격히 떨어진다.

[τ-bench](https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html)는 대화 종료 후 database 상태를 목표 상태와 비교하고, 여러 번 반복했을 때의 신뢰성을 `pass^k`로 본다. [Agent-as-a-Judge](https://proceedings.mlr.press/v267/zhuge25a.html)는 최종 출력뿐 아니라 작업 과정과 단계별 요구사항을 평가하는 방향을 제시한다.

즉 agent eval의 핵심은 다음 세 가지다.

- **Outcome**: 목표 상태가 달성됐는가?
- **Process**: 허용된 경로와 도구로 달성했는가?
- **Reliability**: 같은 조건에서 반복해도 안정적으로 성공하는가?

### 3-4. RAG 평가는 retrieval과 generation을 분리

RAG 답변이 틀렸을 때 원인은 검색 실패, 문맥 선택 실패, 검색된 근거를 무시한 생성, 잘못된 인용 등으로 나뉜다. 최종 답변의 유사도만 재면 원인을 찾을 수 없다.

[RAGAS 논문](https://aclanthology.org/2024.eacl-demo.16/)이 보여주는 대표적 접근은 다음 축을 분리하는 것이다.

- 검색 문맥이 질문과 관련 있는가?
- 필요한 근거를 충분히 회수했는가?
- 답변이 제공된 문맥에 충실한가?
- 답변 자체가 질문에 적절한가?

최근에는 chunking·embedding·retriever·reranker·prompt 조합을 하나의 실험 단위로 보고, component별 지표와 end-to-end task success를 함께 기록하는 패턴이 일반적이다.

### 3-5. offline benchmark와 production trace 평가가 연결

평가가 배포 직전 일회성 보고서에서 개발·운영 루프로 들어오고 있다. [MLflow의 최신 GenAI 평가 문서](https://mlflow.org/docs/latest/genai/eval-monitor/)는 이를 **Evaluation-Driven Development**로 설명하고, [production trace 평가](https://www.mlflow.org/docs/latest/genai/eval-monitor/running-evaluation/traces/)에서는 실제 trace에 ground truth와 scorer를 붙여 재평가하는 흐름을 제공한다.

대표적인 루프는 다음과 같다.

```text
운영 trace·사용자 피드백
        ↓ 표본 추출·익명화
실패 사례를 eval dataset에 추가
        ↓
prompt / model / RAG / agent 변경안 비교
        ↓ 회귀 gate
배포
        ↓
운영 중 sampling eval·품질 모니터링
```

이 흐름에서는 eval dataset, rubric, judge 버전, prompt, model, application commit을 함께 버전 관리해야 한다. 점수만 저장하고 평가 조건을 저장하지 않으면 재현이 불가능하다.

### 3-6. eval-as-code와 CI/CD gate

[Promptfoo](https://github.com/promptfoo/promptfoo)처럼 YAML/CLI로 prompt·model·assertion matrix를 정의하고 CI/CD에서 자동 실행하는 도구가 주목받는 이유는 평가를 반복 가능한 소프트웨어 테스트로 만들기 때문이다. [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai)는 tool use, multi-turn dialog, model-graded eval과 확장 가능한 scorer를 지원해 agent·안전 평가 쪽으로 범위를 넓힌다.

다만 “LLM eval은 unit test”라는 비유는 절반만 맞다.

- schema, 금칙어, tool argument, database state는 unit test처럼 pass/fail이 가능하다.
- 자유 형식 품질은 확률적이며 judge·표본·신뢰구간·사람 검토가 필요하다.
- 모델 업데이트나 provider 변경으로 judge 자체도 drift할 수 있다.

따라서 CI에는 빠르고 결정론적인 smoke set을 넣고, 비용이 큰 judge·red-team·load test는 nightly 또는 release gate로 분리하는 편이 현실적이다.

### 3-7. 품질·안전·성능·비용을 동시에 보는 다목적 평가

최고 품질 모델이 항상 최적의 서비스는 아니다. 실제 선택은 다음 조건을 함께 만족해야 한다.

```text
품질 점수 ≥ 업무 기준
안전 위반률 ≤ 허용 기준
P95 latency ≤ SLO
처리량 ≥ 목표
요청당 비용 ≤ 예산
반복 성공률 ≥ 신뢰성 기준
```

이 때문에 단일 leaderboard 순위보다 **threshold를 통과한 후보 중 비용·지연·운영성을 비교하는 방식**이 더 중요해지고 있다.

---

## 4. 커뮤니티 평가 도구 지형

| 범주 | 대표 프로젝트 | 강점 | 주의점 |
|---|---|---|---|
| 표준 모델 benchmark | [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness), LightEval, HELM | 모델 간 비교, 표준 task, 재현성 | 실제 업무·RAG·agent 품질을 그대로 대표하지 않음 |
| 개발자 중심 app eval | [Promptfoo](https://github.com/promptfoo/promptfoo), DeepEval | prompt/model matrix, assertion, CI/CD | 대규모 cluster scheduling·tenant governance는 별도 |
| RAG 평가 | [RAGAS](https://github.com/vibrantlabsai/ragas) | retrieval와 generation 품질 분해 | judge·합성 metric을 실제 사용자 성과와 보정해야 함 |
| agent·안전 평가 framework | [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | multi-turn, tool use, sandbox, scorer 확장 | 환경 fixture와 실행 비용이 큼 |
| 관찰성·운영 평가 | [MLflow](https://mlflow.org/docs/latest/genai/), Phoenix, Langfuse, LangSmith | trace, feedback, 실험 비교, production sampling | 계측을 애플리케이션에 심어야 함 |
| red teaming | [Garak](https://github.com/NVIDIA/garak), Promptfoo red team | 공격 probe와 취약점 분류 | 탐지 결과를 실제 정책·guardrail 회귀 테스트로 연결해야 함 |
| agent benchmark | [τ-bench](https://github.com/sierra-research/tau-bench), [SWE-bench](https://github.com/SWE-bench/SWE-bench) | 실제 도구·환경 상태 기반 성공 측정 | 특정 domain·scaffold 결과를 모든 업무에 일반화할 수 없음 |

도구 이름보다 중요한 선택 기준은 다음과 같다.

1. **무엇이 평가 단위인가**: 모델 응답, RAG trace, agent trajectory, 최종 시스템 상태
2. **무엇이 정답인가**: reference, rubric, executable test, human preference, business KPI
3. **언제 실행하는가**: 로컬 개발, PR, nightly, release, production sampling
4. **결과를 어떻게 재현하는가**: dataset·prompt·model·judge·코드 버전과 원본 sample 보존
5. **어디서 실행하는가**: SaaS, 온프레미스, air-gap, GPU cluster

---

## 5. RHOAI의 LM-Eval은 무엇인가

RHOAI 3.5 문서에서 **LM-Eval-aaS**는 TrustyAI Operator에 통합된 모델 평가 서비스다. 기반 오픈소스는 다음 두 개다.

- [EleutherAI LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness): 표준 language model benchmark 실행
- [IBM Unitxt](https://www.unitxt.ai/): dataset card, template, task, metric, system prompt를 조합한 평가 recipe

사용자는 `LMEvalJob` Custom Resource를 만들고, operator가 실제 Kubernetes Job을 실행해 결과를 CR status와 log/output에 기록한다.

```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: LMEvalJob
metadata:
  name: model-regression
spec:
  model: local-chat-completions
  modelArgs:
    - name: model
      value: my-model
    - name: base_url
      value: https://model.example/v1/chat/completions
  taskList:
    taskNames:
      - mmlu
  batchSize: "1"
  logSamples: true
```

### LM-Eval의 강점

- `hf`, OpenAI-compatible API, local completion/chat endpoint 등 여러 model backend 평가
- MMLU·HellaSwag·ARC·GSM8K 등 LM Evaluation Harness task 사용
- Unitxt로 custom dataset·template·metric·system prompt 구성
- `LMEvalJob` 단위의 선언적·재현 가능한 실행
- PVC·S3를 이용한 output 및 disconnected/offline 평가
- `allowOnline`, `allowCodeExecution`의 cluster 전역 + job별 이중 보안 gate
- sample별 input/output 보존 옵션
- Unitxt custom metric을 이용한 **LLM-as-a-Judge** 구성
- OpenShift namespace·ServiceAccount·resource quota와 결합 가능

### LM-Eval의 본질적 범위

LM-Eval은 **모델 endpoint에 시험 prompt를 보내고 응답을 metric으로 채점하는 batch evaluation engine**이다. 따라서 다음은 LM-Eval 단독의 중심 기능이 아니다.

- 실제 사용자의 multi-step production trace 분석
- agent tool trajectory와 외부 database 최종 상태 검증
- 지속적인 online sampling과 사용자 피드백 수집
- 사람 annotator 작업 할당과 judge calibration workflow
- RAG component별 원인 분석
- 대규모 부하에서 TTFT·ITL·throughput 측정

RHOAI에서는 이 빈 영역을 LM-Eval 하나에 넣기보다 EvalHub와 다른 provider·MLflow로 분리한다.

---

## 6. RHOAI Evaluation Stack: LMEval을 넘어선 확장

[RHOAI 3.5 Evaluating AI systems](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html-single/evaluating_ai_systems/index)은 LM-Eval과 별도로 **EvalHub**를 평가 orchestration service로 설명한다.

```text
Dashboard / REST / Python SDK / CLI / MCP client
                       |
                       v
                    EvalHub
   provider registry · collection · threshold · tenant/RBAC
                       |
          +------------+-------------+-------------+
          |            |             |             |
          v            v             v             v
    LM Eval Harness   Garak       GuideLLM      LightEval
      model eval     security     performance    model eval
          |
          +---- custom provider / RAGAS 등 확장
                       |
                       v
              Kubernetes Job + sidecar
                       |
                       v
               EvalHub DB / MLflow
```

### 3.5 문서에서 확인되는 주요 기능

- versioned REST API, Python SDK, CLI
- provider adapter를 container image로 등록하는 확장 구조
- benchmark 여러 개를 reusable collection으로 묶기
- benchmark·collection·provider level threshold와 전체 pass/fail
- benchmark별 Kubernetes Job 격리와 병렬 실행
- namespace 기반 multi-tenancy와 Kubernetes RBAC
- Kueue를 통한 queue·quota·admission 연동
- 결과의 MLflow 기록
- custom provider와 custom dataset
- MCP를 통한 coding agent의 평가 job 제출·상태 조회·비교

3.5 문서의 built-in provider 표에는 LM Evaluation Harness 167개 benchmark, Garak 8개, GuideLLM 7개, LightEval 24개가 기재돼 있다. 이 숫자는 release별로 달라질 수 있으므로 운영 시 설치 버전의 provider catalog를 확인해야 한다.

### 라이프사이클 주의

RHOAI 3.5 release notes 기준으로 기능의 지원 수준이 섞여 있다.

| 기능 | 3.5 문서상 상태·주의 |
|---|---|
| `LMEvalJob` 기반 LM-Eval | 정식 평가 guide에 포함된 기존 핵심 workflow |
| 기존 LM-Eval dashboard UI | Technology Preview |
| Evaluation Stack control plane | Developer Preview로 소개 |
| EvalHub SDK·CLI | Technology Preview |
| Evaluation Stack UI | Technology Preview |
| Automated Risk Assessment | Technology Preview |
| MLflow Operator | RHOAI 3.4부터 managed component·fully supported |

즉 평가 control plane의 방향성은 분명하지만, **production support가 필요한 고객 환경에서는 기능별 lifecycle과 SLA 범위를 release notes에서 다시 확인해야 한다.**

공식 근거:

- [RHOAI 3.5 Evaluating AI systems PDF](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/pdf/evaluating_ai_systems/Red_Hat_OpenShift_AI_Self-Managed-3.5-Evaluating_AI_systems-en-US.pdf)
- [RHOAI 3.5 Technology Preview features](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)
- [RHOAI 3.5 Developer Preview features](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)

---

## 7. 커뮤니티 동향과 RHOAI 비교

범례: **강함** = 제품에 명확한 기본 경로가 있음, **부분** = 가능하지만 추가 설계·custom adapter가 필요, **외부** = 별도 도구·계측이 중심

| 평가 요구 | 커뮤니티의 현재 방향 | LM-Eval 단독 | RHOAI Evaluation Stack 전체 | 판단 |
|---|---|---:|---:|---|
| 공개 표준 benchmark | 재현 가능한 baseline·회귀 검사 | **강함** | **강함** | RHOAI의 대표 강점 |
| custom domain dataset | private gold set과 업무별 slice | **강함** | **강함** | Unitxt/custom provider 활용 |
| LLM-as-a-Judge | rubric judge + calibration + meta-eval | **부분** | **부분** | Unitxt로 가능하지만 judge 검증 workflow는 직접 설계 |
| dynamic/live benchmark | 오염을 줄이는 갱신형 시험 | **부분** | **부분** | dataset 갱신 pipeline 또는 custom provider 필요 |
| RAG 평가 | retrieval·faithfulness·answer 품질 분리 | 약함 | **강함/부분** | RAGAS는 인접 provider; 실제 업무 set 보정 필요 |
| agent 결과 평가 | tool·policy·최종 환경 상태·반복 신뢰성 | 약함 | **부분** | MCP는 eval 호출 수단이지 trajectory scorer 자체는 아님 |
| production trace eval | 실제 trace sampling·online monitoring | 외부 | **부분** | EvalHub 결과 추적과 app trace 평가는 구분해야 함 |
| human feedback | annotator·expert review·disagreement 처리 | 외부 | 외부/부분 | MLflow 또는 별도 labeling workflow 필요 |
| 안전·red team | 공격 생성·취약점 분류·회귀 | 외부 | **강함/부분** | Garak·Risk Assessment 제공, 일부 TP |
| 성능·용량 | latency·throughput·SLO·cost | 외부 | **강함/부분** | GuideLLM 연계, 품질 score와 함께 판단 |
| CI/CD gate | 빠른 smoke + nightly/release suite | CR/API로 가능 | **강함/부분** | EvalHub threshold와 pipeline 연동 필요 |
| air-gap·보안 | local eval, 데이터·모델 유출 방지 | **강함** | **강함** | OpenShift와 RHOAI가 특히 유리 |
| multi-tenancy·quota | 조직 단위 격리와 GPU scheduling | 부분 | **강함** | RBAC·namespace·Kueue 강점 |
| 결과 재현·추적 | dataset/model/judge/app 버전 연결 | 부분 | **강함/부분** | MLflow 연계는 좋지만 app commit·judge version 규칙 필요 |

### 핵심 차이

1. **커뮤니티 도구는 개발자 workflow에 가깝다.** 로컬 CLI, YAML, pytest, GitHub Actions에서 빠르게 실행한다.
2. **RHOAI는 플랫폼 workflow에 강하다.** air-gap, tenant, RBAC, resource quota, Kubernetes Job, GPU scheduling, 중앙 결과 추적이 장점이다.
3. **에이전트·운영 평가에서는 서로 보완적이다.** Inspect·Promptfoo 같은 평가 코드를 EvalHub custom provider나 OpenShift Pipeline Job으로 실행하는 조합이 자연스럽다.
4. **LMEval과 EvalHub를 혼동하면 안 된다.** LMEval은 engine/provider이고 EvalHub는 여러 평가 backend를 묶는 control plane이다.

---

## 8. RHOAI에 권장하는 평가 아키텍처

### 8-1. 계층별 도구 배치

```text
[Git / CI]
  prompt·app code·eval dataset·rubric·threshold 버전 관리
       |
       | PR: 결정론적 smoke eval
       v
[EvalHub API / Pipeline]
  collection, threshold, tenant, queue, result orchestration
       |
       +-- LM-Eval: 공개 benchmark + private domain set
       +-- RAGAS: retrieval / faithfulness / answer quality
       +-- Garak: jailbreak / prompt injection / harmful content
       +-- GuideLLM: latency / throughput / SLO
       +-- Custom provider: agent tool trace / database end state
       |
       v
[MLflow]
  model·prompt·dataset·judge·app version, metric, sample, artifact
       ^
       |
[Production observability]
  trace sampling, user feedback, error case → 다음 eval dataset
       |
       +-- 불일치·고위험 sample → human review
```

### 8-2. 실행 주기

| 시점 | 평가 내용 | 목적 |
|---|---|---|
| 개발 로컬 | 소수 gold case, schema·금칙어·tool argument | 빠른 피드백 |
| Pull Request | deterministic assertion + 저비용 judge smoke | 명백한 회귀 차단 |
| Nightly | domain set, RAG slice, 반복 trial | 확률적 회귀와 slice별 약점 확인 |
| Release gate | 표준 benchmark, red team, 성능·비용, human spot check | 배포 승인 근거 |
| Production | trace sampling, 사용자 feedback, 이상 case 수집 | 실제 분포의 drift·신규 실패 탐지 |

### 8-3. 반드시 함께 버전 관리할 항목

- evaluation dataset와 split
- dataset 생성·익명화 방법
- prompt와 system prompt
- model ID·revision·serving parameter
- retrieval 설정과 corpus revision
- tool schema와 agent workflow revision
- metric·rubric·judge model·judge prompt
- random seed, temperature, 반복 횟수
- application Git commit과 container image digest
- threshold 변경 이력과 승인 근거

---

## 9. 도입 순서 제안

### 1단계: 평가 기준부터 정의

도구를 먼저 설치하지 말고 실제 실패를 기준으로 scorecard를 만든다.

| 기준 | 예시 질문 | 우선 채점 방식 |
|---|---|---|
| 정답성 | 답이 사실·계산·업무 규칙에 맞는가? | executable/deterministic → judge 보조 |
| 근거성 | 답이 제공된 문서에 근거하는가? | citation 검사 + RAG judge |
| 업무 성공 | 외부 시스템이 목표 상태가 됐는가? | database/API state assertion |
| 정책 준수 | 금지된 도구·데이터를 사용하지 않았는가? | trace rule + security eval |
| 표현 품질 | 명확하고 유용하며 형식이 맞는가? | schema + rubric judge |
| 성능 | 사용자 SLO를 만족하는가? | GuideLLM/metrics |
| 비용 | 품질 기준 안에서 예산을 만족하는가? | token·GPU·request cost |

### 2단계: LMEval로 baseline 구축

- 후보 모델에 같은 표준 collection을 실행한다.
- 공개 benchmark 외에 업무별 private Unitxt task를 추가한다.
- aggregate score만 보지 말고 category와 sample failure를 보존한다.
- model revision, chat template, few-shot, generation parameter를 고정한다.

### 3단계: EvalHub와 MLflow로 운영화

- 반복 사용하는 benchmark를 collection으로 묶는다.
- threshold를 release gate와 연결한다.
- tenant·RBAC·Kueue queue를 팀별로 분리한다.
- MLflow experiment에 model·dataset·prompt·judge·app revision을 tag로 남긴다.

### 4단계: RAG·안전·성능 provider 추가

- RAG는 retrieval과 generation metric을 분리한다.
- Garak 결과를 일회성 report로 끝내지 말고 재현 prompt를 regression set에 넣는다.
- GuideLLM 부하 결과와 품질 점수를 함께 보고 모델·GPU·serving 설정을 고른다.

### 5단계: agent·production 평가 확장

- agent task마다 fixture, 허용 tool, 금지 action, 목표 최종 상태를 정의한다.
- 같은 task를 여러 번 실행해 평균뿐 아니라 worst case와 반복 성공률을 본다.
- 실제 trace의 실패 사례를 익명화해 private eval set으로 승격한다.
- judge disagreement와 고위험 sample은 human review queue로 보낸다.

---

## 10. 흔한 실패 패턴

| 실패 | 왜 문제인가 | 개선 |
|---|---|---|
| MMLU 점수만으로 모델 선정 | 실제 prompt·domain·RAG·agent를 반영하지 않음 | 표준 benchmark + private task set 병행 |
| 전체 평균만 보고 slice를 무시 | 특정 언어·업무·위험군의 치명적 실패가 숨음 | domain·난이도·risk별 slice score 기록 |
| judge 점수를 ground truth로 취급 | bias·drift·prompt sensitivity가 있음 | human gold set으로 judge calibration |
| 한 번 성공한 agent를 합격 처리 | 비결정성 때문에 반복 신뢰성이 낮을 수 있음 | 반복 trial과 pass^k·worst case 확인 |
| RAG 최종 답만 채점 | retriever와 generator 중 원인을 구분 못함 | retrieval·faithfulness·answer 분리 |
| 결과 metric만 저장 | 실패 sample과 평가 조건을 재현할 수 없음 | sample·artifact·모든 version 보존 |
| eval set을 영구 고정 | contamination·saturation·업무 drift 발생 | production 실패를 반영해 지속 갱신 |
| preview 기능을 production SLA로 전제 | 지원 범위와 upgrade risk가 다름 | RHOAI release별 lifecycle 확인 |

---

## 11. 최종 판단

### RHOAI LMEval이 잘 맞는 경우

- 여러 open model을 같은 benchmark로 비교해야 한다.
- OpenShift 안에서 재현 가능한 batch evaluation이 필요하다.
- air-gap·보안·RBAC·resource quota가 중요하다.
- custom domain dataset을 Unitxt로 표준화하려 한다.
- 평가 결과를 EvalHub·MLflow로 중앙 관리하려 한다.

### LMEval만으로 부족한 경우

- 실제 사용자 trace를 지속 평가해야 한다.
- RAG 검색 단계의 원인을 세밀하게 분석해야 한다.
- multi-step agent의 tool call·정책·최종 상태를 검증해야 한다.
- 사람 피드백과 judge calibration을 운영해야 한다.
- 품질뿐 아니라 red team·latency·throughput·cost를 release gate로 묶어야 한다.

### 권장 포지셔닝

> **LM-Eval = 모델 평가 실행 엔진**  
> **EvalHub = 평가 control plane**  
> **MLflow = 결과·실험·trace 연결 계층**  
> **RAGAS/Garak/GuideLLM/custom provider = 평가 전문 backend**  
> **private gold set + human review = 조직 고유의 신뢰 기준**

RHOAI는 커뮤니티 평가 도구를 대체하는 폐쇄형 단일 제품이라기보다, 여러 오픈소스 평가 엔진을 OpenShift의 보안·격리·스케줄링·운영 모델 안에서 실행하는 플랫폼으로 보는 편이 정확하다.

---

## 12. 참고 자료

### 연구·benchmark

- [LiveBench: A Challenging, Contamination-Limited LLM Benchmark — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/e4a46394ba5378b3f9a186a5b4c650d1-Abstract-Conference.html)
- [Benchmarking Large Language Models Under Data Contamination — EMNLP 2025](https://aclanthology.org/2025.emnlp-main.511/)
- [Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/fdca08d371e4b6c031397909e20043bd-Abstract-Conference.html)
- [Agent-as-a-Judge: Evaluate Agents with Agents — ICML 2025](https://proceedings.mlr.press/v267/zhuge25a.html)
- [τ-bench: Tool-Agent-User Interaction in Real-World Domains — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html)
- [RAGAS: Automated Evaluation of Retrieval Augmented Generation — EACL 2024](https://aclanthology.org/2024.eacl-demo.16/)

### 오픈소스·운영 도구

- [EleutherAI LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness)
- [Unitxt](https://www.unitxt.ai/)
- [EvalHub](https://github.com/opendatahub-io/eval-hub)
- [MLflow GenAI Evaluation and Monitoring](https://mlflow.org/docs/latest/genai/eval-monitor/)
- [Promptfoo](https://github.com/promptfoo/promptfoo)
- [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai)
- [RAGAS](https://github.com/vibrantlabsai/ragas)
- [Garak](https://github.com/NVIDIA/garak)

### Red Hat OpenShift AI

- [RHOAI 3.5 Evaluating AI systems](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html-single/evaluating_ai_systems/index)
- [RHOAI 3.5 Evaluating AI systems PDF](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/pdf/evaluating_ai_systems/Red_Hat_OpenShift_AI_Self-Managed-3.5-Evaluating_AI_systems-en-US.pdf)
- [RHOAI 3.5 Technology Preview features](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes)
- [RHOAI 3.5 Developer Preview features](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/developer-preview-features_relnotes)

> 문서의 수치와 lifecycle은 2026-07-21에 확인한 RHOAI 3.5 문서를 기준으로 한다. 이후 release에서는 provider 수, 지원 수준, API가 달라질 수 있다.
