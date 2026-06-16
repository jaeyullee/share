# RAG 아키텍처 핵심정리

> OCP 엔지니어 관점 | 2026-04-10 | 예상 읽기 시간: 10분

---

## 1. RAG가 뭔데?

**RAG = Retrieval-Augmented Generation**. 직역하면 "검색으로 보강된 생성"이다.

LLM은 학습 시점까지의 공개 데이터만 안다. 회사 내부 문서, 최신 장애 보고서, 우리 팀 런북은 모른다. 그래서 "환각(hallucination)"이 생긴다. 없는 걸 있다고 지어내는 것.

RAG는 이 문제를 이렇게 푼다:

> **"답하기 전에 먼저 찾아봐라."**

사용자 질문이 들어오면, LLM이 바로 답하는 게 아니라 먼저 내부 문서 저장소에서 관련 내용을 검색한다. 그 검색 결과를 프롬프트에 붙여서 LLM에게 넘긴다. LLM은 그 컨텍스트를 바탕으로 답한다.

### OCP 비유

> OCP 클러스터에서 `oc describe pod`를 먼저 실행하고 나서 트러블슈팅하는 것과 같다. 아무 정보 없이 추측하는 게 아니라, 실제 상태를 먼저 조회하고 판단한다.

---

## 2. RAG 파이프라인 구조

RAG는 두 개의 독립적인 파이프라인으로 구성된다.

```
[Ingestion Pipeline]          [Query Pipeline]
문서 수집                      사용자 질문
   ↓                              ↓
청킹(Chunking)               질문 임베딩 생성
   ↓                              ↓
임베딩 생성                   벡터 DB 유사도 검색
   ↓                              ↓
벡터 DB 저장                  관련 청크 추출
                                  ↓
                             프롬프트 조립 (질문 + 컨텍스트)
                                  ↓
                             LLM 추론
                                  ↓
                             응답 반환
```

두 파이프라인을 분리하는 이유가 있다. 문서 적재는 배치로 미리 해두고, 질의응답은 실시간으로 처리해야 하기 때문이다. 섞으면 확장성이 무너진다.

### 각 단계 설명

| 단계 | 설명 | OCP 비유 |
|------|------|----------|
| **청킹** | 문서를 작은 단위로 분할 | ConfigMap을 섹션별로 나누는 것 |
| **임베딩** | 텍스트를 숫자 벡터로 변환 | 텍스트를 좌표로 변환해 지도에 찍는 것 |
| **벡터 DB** | 임베딩 저장 + 유사도 검색 | etcd가 클러스터 상태를 저장하듯, 지식을 저장 |
| **유사도 검색** | 질문 벡터와 가장 가까운 청크 찾기 | `grep`이 아니라 "의미가 비슷한 것" 찾기 |
| **컨텍스트 주입** | 검색 결과를 프롬프트에 삽입 | 런북을 열어서 LLM 앞에 펼쳐놓는 것 |

---

## 3. 벡터 DB 선택지

| 벡터 DB | 특징 | 적합한 상황 |
|---------|------|-------------|
| **pgvector** | PostgreSQL 확장, SQL로 검색 | 기존 PG 인프라 있을 때, 디버깅 중시 |
| **ChromaDB** | 경량, 로컬 개발 친화적 | PoC, 로컬 실험 |
| **Milvus** | 대규모 분산, 고성능 | 프로덕션, 대용량 문서 |
| **Qdrant** | OCI 이미지 지원, RamaLama 연동 | 컨테이너 기반 배포 |
| **In-memory** | Llama Stack 기본 제공 | 개발/테스트 전용 |

### pgvector 유사도 검색 SQL 예시

```sql
SELECT content, source,
       1 - (embedding <=> :queryEmbedding::vector) AS similarity
FROM chunks
WHERE 1 - (embedding <=> :queryEmbedding::vector) > 0.7
ORDER BY embedding <=> :queryEmbedding
LIMIT 5;
```

`<=>` 연산자가 코사인 거리를 계산한다. 결과가 1에 가까울수록 유사하다.

---

## 4. 엔터프라이즈 RAG 아키텍처

단순 PoC와 운영 환경의 차이는 크다.

```
[사용자]
   ↓
[Frontend UI]
   ↓
[Llama Stack API]  ← 표준 API 계층
   ↓
[에이전트 레이어]
   ├── Guard Rails (가드레일)
   ├── Model Servers (vLLM / Ollama)
   ├── Tools (Tavily 웹검색 등)
   └── Vector DBs (부서별 분리)
```

### 엔터프라이즈 RAG의 4가지 요구사항

| 요구사항 | 설명 | OCP 비유 |
|----------|------|----------|
| **보안** | 가드레일로 유해 출력 차단, 민감정보 보호 | NetworkPolicy로 트래픽 제어하는 것 |
| **멀티테넌시** | 부서별 벡터 DB 분리 (HR, 법무, 구매 등) | Namespace로 팀별 격리하는 것 |
| **거버넌스** | 어떤 문서가 어떤 답변에 쓰였는지 추적 | Audit log로 API 호출 기록하는 것 |
| **확장성** | 대량 문서 + 동시 사용자 처리 | HPA로 Pod 자동 확장하는 것 |

### Red Hat 엔터프라이즈 RAG 기술 스택

```
플랫폼:     OpenShift AI (ServingRuntime, InferenceService CRD)
모델 서빙:  vLLM
API 계층:   Llama Stack
벡터 DB:    PGVector
스토리지:   MinIO (S3 호환)
파이프라인: Kubeflow Pipelines
배포:       Helm 차트
외부 검색:  Tavily API
```

---

## 5. 직접 RAG vs 에이전트 RAG

두 방식의 차이를 명확히 이해해야 한다.

### 직접 RAG (Completion API 방식)

```
앱이 직접:
1. 벡터 DB 검색 실행
2. 검색 결과를 프롬프트에 조립
3. LLM chatCompletion 호출
```

**장점**: 검색 쿼리와 프롬프트를 완전히 제어. 디버깅 쉬움. 비용 낮음.
**단점**: 코드가 더 많음.

### 에이전트 RAG (Agent API 방식)

```
앱이:
1. 에이전트 생성 (RAG 도구 연결)
2. 질문 전달

에이전트가 내부적으로:
1. 도구 호출 여부 판단
2. 벡터 검색 실행
3. 결과 활용해 응답 생성
```

**장점**: 코드 단순. 도구 호출 자동화.
**단점**: 내부 검색 쿼리 통제 불가. 양자화 모델에서 도구 호출 실패 가능.

### 선택 기준

```
디버깅/비용 중시 → Completion API 방식
코드 단순성 중시 + 고성능 모델 사용 → Agent API 방식
```

---

## 6. RAG 파인튜닝 (고급)

기본 RAG는 사전학습된 모델을 그대로 쓴다. 파인튜닝 RAG는 검색기와 생성기를 함께 최적화한다.

### Joint Training 구조

```
[질문] → DPR Question Encoder → 검색 쿼리 임베딩
                                        ↓
                              Feast + Milvus 검색
                                        ↓
[검색된 패시지] → BART Generator → 최종 답변
```

두 모델(인코더 + 생성기)이 함께 학습된다. 검색기가 "생성에 실제로 도움이 되는 문서"를 찾도록 최적화된다.

### OpenShift AI에서 분산 학습

```yaml
# Kubeflow PyTorchJob으로 실행
apiVersion: kubeflow.org/v1
kind: PyTorchJob
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
    Worker:
      replicas: N  # GPU 수에 따라
```

FSDP(Fully Sharded Data Parallel)로 멀티 GPU 분산 학습을 수행한다.

---

## 7. RamaLama로 RAG 컨테이너화

RamaLama는 AI 모델과 RAG 데이터를 OCI 이미지로 패키징해 배포한다.

```bash
# 문서로 RAG 벡터 DB 생성
ramalama rag ./docs/

# RAG 붙인 챗봇 실행
ramalama run --rag ./docs/ granite3.1-dense:8b

# REST API로 서빙
ramalama serve --rag ./docs/ granite3.1-dense:8b

# OCI 이미지로 변환 후 배포
ramalama convert MODEL
ramalama push quay.io/myorg/my-rag-model:latest
```

### 배포 대상

| 환경 | 방법 |
|------|------|
| 엣지 디바이스 | `--generate quadlet` |
| Kubernetes/OCP | `--generate kube` |

문서 파싱은 **Docling**이 담당한다. PDF, DOCX, Markdown을 구조화된 JSON으로 변환한다. 벡터 DB는 현재 **Qdrant**를 사용한다.

---

## 8. 핵심 원칙 정리

1. **단순하게 시작한다.** pgvector + SQL로 기준선을 만들고, 실패 사례를 보고 나서 복잡도를 높인다.
2. **두 파이프라인을 분리한다.** Ingestion과 Query는 독립적으로 운영한다.
3. **청킹 전략이 품질을 결정한다.** 청크 크기와 overlap을 실험해야 한다.
4. **유사성 ≠ 정확성.** threshold와 topK를 튜닝해야 한다.
5. **컨텍스트가 없으면 답하지 않는다.** 환각보다 "정보 없음" 응답이 낫다.

---

## 참고 소스

- 엔터프라이즈 RAG 챗봇으로 회사 지식을 중앙 집중화하세요 (Red Hat 문서)
- Red Hat OpenShift AI를 사용하여 엔터프라이즈 RAG 챗봇 배포 (Red Hat 개발자)
- LLM과 RAG를 활용하여 생성형 AI를 한 단계 업그레이드하세요 (Red Hat 개발자)
- 지루한 RAG: 유사성 검사가 단순히 SQL 쿼리일 때 (레드햇 개발자)
- Llama Stack과 Node.js/Python을 활용한 검색 증강 생성 (Red Hat 개발자)
- Feast와 Kubeflow Trainer를 사용하여 RAG 모델을 세밀하게 조정하는 방법 (Red Hat 개발자)
- RamaLama와 RAG를 사용하여 AI 데이터 통합을 간소화하세요 (Red Hat 개발자)
- Node.js, Podman AI Lab 및 React를 활용한 검색 증강 생성 (Red Hat 개발자)
