# RAG — 데모 관점 정리 (enabler)

> `generative-ai-rag`(#9) + `rag-llm-gitops`(#6) + `genai-rhoai-poc-template`(#11) + Llama Stack RAG(#4,#5)에서 추출.
> RAG **이론**은 [01-RAG-아키텍처-핵심정리](../../4-etc-AI-materials/01-RAG-아키텍처-핵심정리.md)에 깊게 있음. 이 노트는 **데모들이 RAG를 어떻게 보여주고 구현하는가**(실전·셀링)에 집중.

---

## 1. RAG가 푸는 문제 (고객 메시지)

- 일반 LLM의 한계: **지식 노후**(학습 커트오프) + **할루시네이션** + **기업 독점지식 부재**.
- 대안 비교: 모델 재학습/파인튜닝(수주~수개월, 데모 표현 $100K~$500K) **vs** RAG(문서 추가, 데모 표현 분 단위/저비용).
- RAG = "모델은 그대로, **검색으로 컨텍스트를 주입**". 거버넌스(출처 인용)·규정대응에 유리.

---

## 2. RAG 2단계 / 3페이즈

```
[Indexing] 문서 로드 → 청킹(500~1000토큰, 오버랩) → 임베딩 → 벡터 DB 저장
[Runtime]  질의 임베딩 → 의미 유사도 검색(Top-K 3~5) → 프롬프트에 주입 → LLM 생성(+인용)
```

- 청킹 트레이드오프: 너무 크면 노이즈/비용↑, 너무 작으면 컨텍스트 손실 → 오버랩으로 보완.
- **하이브리드 검색**(#5): 의미검색 + 키워드(BM25) 조합으로 정확도/리콜 동시 확보.
- 임베딩은 한 번 생성하면 외부 저장소에 유지(재학습 불필요).

---

## 3. 벡터 DB 선택지 (데모별로 다름)

| 데모 | 벡터 DB | 임베딩 |
|---|---|---|
| generative-ai-rag(#9) | **pgvector**(PostgreSQL 확장) | — |
| rag-llm-gitops(#6) | pgvector(기본)/EDB/Redis/Elasticsearch/MSSQL **선택형** | Sentence-Transformers all-mpnet-base-v2 |
| genai-poc-template(#11) | **Milvus**(+Attu UI) | — |
| llamastack(#4,#5) | Milvus/FAISS/Chroma | all-MiniLM-L6-v2 / Nomic(768d) |

> enabler 포인트: "벡터 DB는 하나가 아니다". pgvector(기존 PG 재활용·간단), Milvus(전용·확장), Redis(저지연), Elasticsearch(대규모) — 고객 기존 스택·규모로 선택. 성능/비용 트레이드오프 설명 가능해야.

---

## 4. RHOAI에서의 GenAI/RAG 구현 자산

- **Workbench(Jupyter)** + **Elyra 시각 파이프라인**(YAML 없이 드래그앤드롭) → 도메인 전문가도 파이프라인 구성.
- **Tekton/OpenShift Pipelines**로 지식 업데이트 자동화(문서추가→벡터화→저장).
- **Data Science Project**로 Workbench/Pipeline/Model Deployment를 한 곳에 묶음.
- 서빙: vLLM(Granite/Mistral/CodeLlama). UI: Gradio / AnythingLLM.
- 자동 품질검증: 검색 정확도·응답 정확도·레이턴시·인용 정확도 측정.

---

## 5. 거버넌스 — 출처 인용이 핵심

- 생성 응답에 **검색 출처(citation)** 표시 → 사용자 신뢰 + 감사 추적 + 규제 대응.
- "어떤 문서가 어떤 답을 만들었나" 추적 가능 = 엔터프라이즈 RAG의 필수 요건.

---

## 6. 멀티 제공자 평가 (rag-llm-gitops #6)

- 같은 질의를 vLLM/OpenAI/HF/NVIDIA NIM에 동시 실행 → **A/B 평가**.
- 사용자가 응답 rating 제출 → Prometheus 메트릭 → Grafana 대시보드에서 제공자별 점수 비교 → 프로덕션 모델 선택.

---

## 7. enabler 핵심 메시지

- 발표용: generative-ai-rag(#9)는 **비즈니스 가치(ROI) → 데모** 흐름이라 임원 대상에 적합. "재학습 vs RAG" 비교가 핵심 슬라이드.
- 구현용: rag-llm-gitops(#6, GitOps 정석) 또는 genai-poc-template(#11, 가벼운 PoC) 중 선택 → [06-GitOps-ValidatedPatterns-PoC배포](06-GitOps-ValidatedPatterns-PoC배포.md)
- 자주 받는 질문 대비: 청킹 전략, 벡터 DB 선택 근거, 임베딩 모델, 할루시네이션 억제(인용·검색품질), 데이터 보안(온프레 배포).
- RAG는 만능 아님 → 실시간/연산형 질의는 도구호출(에이전트)·Agentic RAG와 결합 필요 → [04-에이전트-AI-패턴](04-에이전트-AI-패턴.md)
