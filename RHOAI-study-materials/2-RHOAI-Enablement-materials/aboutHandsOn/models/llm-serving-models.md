# LLM 서빙 모델 (Day 14 MaaS / vLLM · llm-d) — Hugging Face 링크

> Day 14는 GPU 환경(Environment B)에서 수행. 모델은 직접 만들지 않고 HF에서 받는다.

## 권장 모델

| 용도 | 모델 | HF 링크 | 비고 |
|---|---|---|---|
| llm-d 벤치마크 기준(v0.9 명시) | Llama 3.1 8B Instruct | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | GuideLLM P95/P99 비교의 기준 모델 |
| Red Hat 정렬 | Granite 3.1 8B Instruct | https://huggingface.co/ibm-granite/granite-3.1-8b-instruct | OpenAI 호환 API 데모 |
| 초경량 스모크 | Qwen2.5 0.5B Instruct | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 파이프라인 검증 |
| 양자화 | Llama 3.1 8B (AWQ) | https://huggingface.co/models?search=llama-3.1-8b-instruct%20awq | `--quantization awq` |

## vLLM 파라미터 메모

- `--tensor-parallel-size` : GPU 장수
- `--gpu-memory-utilization 0.9` : KV 캐시 여유
- `--max-num-seqs` : 동시 시퀀스(처리량↔지연)
- `--max-model-len` : 컨텍스트 길이(KV 캐시 절약)
- `--quantization awq|gptq` : 메모리 절감

## llm-d 핵심 (Day 14 후반)

- **Prefill vs Decode**: 입력 토큰 일괄 처리(prefill) → 토큰 하나씩 생성(decode). prefill 큐잉이 Tail Latency(P95/P99) 주범.
- **Prefix Cache Aware Routing**: 같은 프리픽스 요청을 같은 백엔드로 보내 KV 캐시 히트율↑ → "GPU 증설 != P95 개선"을 입증.
- **GuideLLM**: TTFT/TPOT/E2E 지연을 측정하는 벤치마크 도구. vLLM 4 replica vs llm-d 비교.

## 서빙 매니페스트

- vLLM ServingRuntime + InferenceService + LLMInferenceService(llm-d): `../manifests/day14-maas-llmd.yaml`
