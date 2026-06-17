# Llama Stack 핵심 (enabler 관점)

> `llamastack-on-ocp`(#4) + `agentic-ai-llamastack`(#5) + `llmaas`(#2)에서 추출.
> "Llama Stack이 대체 뭐고 RHOAI에서 왜 쓰나"를 입문자가 잡는 노트.
> 연결: [01-RHOAI3-신규기능-핵심](01-RHOAI3-신규기능-핵심.md), [04-에이전트-AI-패턴](04-에이전트-AI-패턴.md), [03-MCP-핵심](03-MCP-핵심.md)

---

## 1. 한 줄 정의

**Llama Stack = GenAI 앱의 "비즈니스 로직 계층"을 표준 API로 묶은 오픈소스 프레임워크**(Meta 주도). 추론·RAG·에이전트·안전성·도구·텔레메트리를 한 세트의 API로 제공한다. RHOAI 3에서는 **LlamaStack Operator**로 1급 컴포넌트.

> OCP 비유: vLLM이 "모델을 돌리는 런타임(=컨테이너 런타임)"이라면, Llama Stack은 "그 위에서 앱 로직을 표준 인터페이스로 묶는 미들웨어(=서비스 메시 + SDK)". 모델을 바꿔도 앱 코드(`curl`)는 그대로.

---

## 2. 왜 필요한가 (해결하는 문제)

- LLM 앱마다 RAG·도구호출·안전필터·평가를 **제각각 재구현**하는 낭비를 없앤다.
- **제공자 독립성(provider independence)**: 백엔드(vLLM 로컬 / AWS Bedrock / 원격)를 바꿔도 동일 API. 포트만 바꾸면 `curl` 동일.
- OpenAI 호환 인터페이스(ChatCompletions/Responses) + REST 100+ 엔드포인트 제공 → 기존 생태계 도구 즉시 연동.

---

## 3. 5대 핵심 API (외워둘 것)

| API | 역할 | 데모에서 |
|---|---|---|
| **Inference** | LLM 추론(채팅/완성) | vLLM Granite/Llama 백엔드 |
| **Agents** | 세션·턴 기반 에이전트 오케스트레이션 | ReAct, 도구 체이닝, 멀티턴 |
| **RAG (Vector/Tool)** | 문서 인덱싱·의미검색 | Milvus/FAISS/Chroma, 임베딩 |
| **Safety (Shields)** | 입력/출력 안전 필터 | Llama Guard 3, S1~S7 분류 |
| **Tools** | 도구 등록·호출(웹검색·MCP 등) | Tavily, MCP 서버 |
| (+Telemetry) | 추적/관찰성 | Langfuse 연동 |

---

## 4. 아키텍처 3계층

1. **통합 API 계층(Unified API)**: 위 5대 API의 표준 인터페이스.
2. **배포 계층(Distribution)**: `LlamaStackDistribution` CR → Pod+Service 자동 생성(기본 포트 **8321**). ConfigMap(`run.yaml`)으로 구성.
3. **제공자 어댑터(Provider adapters)**: 각 API 뒤에 실제 구현(vLLM, Bedrock, Milvus, Tavily, Llama Guard 등)을 어댑터로 꽂음.

> 클라이언트-서버 모델: Llama Stack 서버는 별도 서비스, 클라이언트(Python SDK / REST)가 통신. 상태는 `session_id`로 유지 → 서비스 재시작에도 복구.

---

## 5. RHOAI에서의 배포 형태

- **CRD 선언형 배포**: `LlamaStackDistribution`만 만들면 자동 Pod/Service. GenAI Playground가 이를 자동 생성(원클릭).
- 모델은 RHOAI의 vLLM InferenceService를 Inference provider로 연결.
- 컨테이너 분리: 모델 서빙(vLLM Pod) ↔ 앱 로직(Llama Stack Pod) 독립 운영. ConfigMap/env로 엔드포인트·API 키 관리.
- 다중 모델 혼합: 로컬(Granite) + 원격(Llama) 동시 사용 가능.

---

## 6. 에이전트 진화 단계 (llamastack-on-ocp Level 0~6)

1. **단순 RAG**: 벡터 DB 검색 → 답변 (Level 1)
2. **도구 에이전트**: 웹검색 등 도구를 LLM이 호출 (Level 2)
3. **ReAct**: Reason→Act→Observe 반복으로 다단계 추론 (Level 3)
4. **Agentic RAG**: 에이전트가 "RAG를 쓸지" 자율 판단 (Level 4)
5. **MCP 에이전트**: 실제 시스템(OpenShift/Slack) 조작 (Level 5) → [03-MCP-핵심](03-MCP-핵심.md)
6. **통합 자동화**: 인시던트 분석→문서검색(RAG)→인프라조작(MCP)→Slack 보고 (Level 6)

---

## 7. 프로덕션 3대 축 (agentic 데모의 메시지)

- **안전(Shields)**: 입력/도구/출력 3단 방어. Llama Guard 3(1B 경량)로 오버헤드 최소. S1(폭력)~S7(프라이버시) 분류. → [04-에이전트-AI-패턴](04-에이전트-AI-패턴.md)
- **평가(Evals)**: 데이터셋 기반 + 결정론적 스코링 + LLM-as-Judge. **CI/CD 게이트**로 회귀 감지(모델 업그레이드 검증).
- **관찰성(Langfuse)**: traces(LLM·도구 호출 사슬) + evals + 사용자 feedback 루프.

---

## 8. Llama Stack vs LangGraph (둘 다 등장)

| | Llama Stack | LangGraph |
|---|---|---|
| 성격 | 통합 표준 프레임워크 | 그래프 기반 상태 오케스트레이션 |
| 안전(Shields) | 기본 내장 | 별도 구현 필요 |
| 배포 | CRD(LlamaStackDistribution) | FastAPI 마이크로서비스 |
| 강점 | 표준 API·제공자 독립 | 복잡한 상태/분기 워크플로우 |

> 시각 빌더 **Langflow**(드래그앤드롭) + 관찰성 **Langfuse**는 둘 다와 조합 가능.

---

## 9. enabler가 기억할 것

- Llama Stack은 "모델을 호출하는 표준 미들웨어" — vLLM(서빙) 위, 앱(UI/에이전트) 아래.
- 고객에게: "모델·벡터DB·안전모델을 갈아끼워도 앱 코드 안 바뀐다(provider 독립)"가 셀링 포인트.
- RHOAI 3에서 GenAI Playground = Llama Stack 자동화의 사용자 접점.
- 입문 실습 경로: llamastack-on-ocp(#4) Level 1→6 순서대로가 가장 친절.
