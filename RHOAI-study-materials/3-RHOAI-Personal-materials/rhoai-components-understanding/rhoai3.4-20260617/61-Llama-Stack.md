# Llama Stack Operator

> GenAI 앱(RAG/agentic) 통합 런타임. 추론·임베딩·벡터저장·검색·안전·평가·도구를 **OpenAI 호환 API 한 벌**로 추상화.
> 영역: [60-GenAI평가안전-관계](60-GenAI평가안전-관계.md)

---

## 1. 정의 / 역할
- RAG/agentic 워크로드를 표준화. inference/vector_io/safety/eval/tool_runtime을 **프로바이더 플러그인**으로 묶는 허브.

## 2. 버전 / 라이프사이클
- 서버 `llamastack/llama-stack`(0.6.0), 오퍼레이터 `opendatahub-io/llama-stack-k8s-operator`(Go).
- RHOAI 3.4 GA = **0.6.0.1+rhai0**(EA1=0.5.0, 3.3=0.4.2.1).
- **코어 오퍼레이터 GA, 개별 API/프로바이더는 TP/DP 혼재**(chat/completions=TP, responses·embeddings·tool_runtime·vector_io=DP).

## 3. 프로바이더 카테고리 (run.yaml로 선택)
- inference: `remote::vllm`(TP), `remote::openai/bedrock/azure/watsonx`, `inline::sentence-transformers`.
- vector_io: `inline::faiss`, `inline::milvus`, `remote::milvus/pgvector/qdrant`.
- safety: `remote::trustyai_fms` (→ TrustyAI).
- eval: `inline::ragas`, `remote::ragas/lmeval`, Garak.
- tool_runtime: `remote::model-context-protocol`(MCP, DP), `inline::rag-runtime`.
- agents: `inline::meta-reference`(Responses API 백킹).

## 4. CRD: LlamaStackDistribution

| 항목 | 값 |
|---|---|
| group/version | `llamastack.io/v1alpha1` |
| kind / scope | `LlamaStackDistribution`(`llsd`) / Namespaced |

- 핵심 spec: `replicas`, `server.distribution.{name|image}`(둘 중 하나, XValidation), `server.containerSpec`(port 기본 **8321**, env, resources), `server.userConfig.configMapName`(**run.yaml ConfigMap**), `server.storage`(기본 10Gi, `/.llama`), `network.exposeRoute`/`allowedFrom`, `autoscaling`(HPA), `tlsConfig`.
- status: `phase`(Pending/Initializing/Ready/Failed), `distributionConfig.availableDistributions`(가용 배포판 이름 확인처), `serviceURL`/`routeURL`.

```yaml
apiVersion: llamastack.io/v1alpha1
kind: LlamaStackDistribution
metadata: { name: llamastack-prod }
spec:
  replicas: 1
  server:
    distribution: { name: rh-dev }
    containerSpec: { port: 8321 }
    storage: { size: 20Gi }
    userConfig: { configMapName: llama-stack-config }
```

## 5. 배포 산출물 / 활성화
- Deployment(8321) + Service + PVC + run.yaml ConfigMap + NetworkPolicy (+ exposeRoute 시 Route, +HPA/PDB).
- 활성화: DSC `spec.components.llamastackoperator.managementState: Managed`.

## 6. 연동
- **KServe**: vLLM(RawDeployment) 모델을 `remote::vllm`로 연결. agentic엔 `--enable-auto-tool-choice` 필요. → [31-KServe](31-KServe.md)
- **TrustyAI**: `remote::trustyai_fms` safety provider → [62-TrustyAI](62-TrustyAI.md).
- **LMEval**: `remote::lmeval` eval provider → [63-LMEval-Evaluation-Stack](63-LMEval-Evaluation-Stack.md).
- **MCP**: `remote::model-context-protocol` tool provider → [64-AI-Hub](64-AI-Hub.md).
- **PostgreSQL**: 프로덕션 metadata store(v14+) 필수, 개발은 inline 가능.

## 7. 운영 함정
- inline 프로바이더는 **feature-flag 환경변수**(`ENABLE_FAISS`, `ENABLE_INLINE_MILVUS`, `ENABLE_SENTENCE_TRANSFORMERS`)로 켜야 활성.
- OpenAI SDK `base_url`에 **`/v1` 접미사 필수**.
- **Conversations API는 3.4 미확인**(Responses API는 DP 확인).
- 플랫폼: s390x 미지원, ppc64le 제약(milvus-lite/pgvector/FP16 불가).

## 8. 출처
- 오퍼레이터/CRD: https://github.com/opendatahub-io/llama-stack-k8s-operator (`api/v1alpha1/`)
- RHOAI 3.4 working_with_llama_stack
