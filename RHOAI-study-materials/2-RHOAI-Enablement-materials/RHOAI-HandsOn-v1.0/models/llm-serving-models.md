# LLM 서빙 모델 (Day 14 MaaS / vLLM · llm-d) — Hugging Face 링크

> Day 14는 **GPU 랩**에서 수행(홈 SNO엔 GPU 없음). 모델은 직접 만들지 않고 HF에서 받는다.
> 폐쇄망 반입: `huggingface-cli download <repo>` → USB(Proxmox passthrough) → 에어갭 S3 업로드
> (홈서버 00문서 §6 "모델 반입" 절차).

## 권장 모델 (작을수록 단일 5060 Ti 16GB에 적합)

| 용도 | 모델 | HF 링크 | 비고 |
|---|---|---|---|
| 기본 vLLM 서빙(권장, Red Hat 정렬) | Granite 3.1 2B Instruct | https://huggingface.co/ibm-granite/granite-3.1-2b-instruct | IBM/Red Hat 생태계, OpenAI 호환 API 데모에 적합 |
| 초경량 스모크테스트 | Qwen2.5 0.5B Instruct | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 가장 빠른 기동, 파이프라인 검증용 |
| 일반 채팅 | Qwen2.5 7B Instruct | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 16GB 1장에 FP16 빠듯 → 양자화 권장 |
| 양자화(메모리 절감) | Llama 3.1 8B Instruct (AWQ/GPTQ) | https://huggingface.co/models?search=llama-3.1-8b-instruct%20awq | `--quantization awq` |
| Guardrails detector(Day 13) | Granite Guardian 3.1 2B | https://huggingface.co/ibm-granite/granite-guardian-3.1-2b | TrustyAI/Guardrails 콘텐츠·PII 탐지 백엔드 후보 |
| 임베딩(선택) | BGE small en v1.5 | https://huggingface.co/BAAI/bge-small-en-v1.5 | RAG 데모 확장 시 |

## vLLM 서빙 파라미터 메모 (GPU 트랙 학습플랜과 연계)

- `--tensor-parallel-size` : GPU 장수(5060 Ti는 NVLink 없음 → TP보다 단일카드 권장)
- `--gpu-memory-utilization 0.9` : KV 캐시 여유
- `--max-num-seqs` : 동시 시퀀스(처리량 vs 지연 트레이드오프)
- `--quantization awq|gptq` : 16GB에 큰 모델 올릴 때
- `--max-model-len` : 컨텍스트 길이 축소로 KV 캐시 절약

## 서빙 매니페스트

- vLLM ServingRuntime + InferenceService: `../manifests/day14-maas-llm/`
- llm-d / GuideLLM 벤치마크는 GPU 트랙 학습플랜(`006-006-RHOAI-학습플랜-GPU.md`) §2 참조.

## CPU에서 LLM을 꼭 한 번 띄워보려면 (선택, 성능 무의미)

홈 SNO(CPU)에서 경로만 체득하려면 가장 작은 모델(Qwen2.5 0.5B)을 vLLM CPU 백엔드 또는
llama.cpp(GGUF)로 띄워볼 수 있다. **응답은 느리며 데모/성능용 아님 — 경로 확인용.**
