---
title: Get started with AI Inference (e-book) 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - inference
  - quantization
  - vllm
source: Get started with AI Inference.PDF
---

# Get started with AI Inference (e-book) 정리

> 원본: `Get started with AI Inference.PDF` — 추론 성능 엔지니어링·모델 최적화 입문서. 양자화·sparsity·vLLM 기초.
> 상위 맥락: [[00-인덱스]] / 심화는 [[03-AI-Inference-기술개요]]

---

## 1. 핵심 용어

- **Activations** — 모델이 입력 처리 중 생성하는 임시 데이터(중간 결과). 보통 높은 정밀도 필요.
- **Weights** — 학습된 파라미터(설정값). 낮은 정밀도에서도 효과적으로 동작 가능.
- **Quantization(양자화)** — 가중치·활성값을 저비트로 저장해 크기·자원 요구 감소(파일 압축과 유사).
  - Weight 양자화 / Activation 양자화 / **KV cache 양자화**(긴 프롬프트·동시요청 효율).
  - 정밀도: **16-bit(FP16/BF16)** 표준 / **8-bit(FP8/INT8)** 메모리 절반·정확도 유지 / **4-bit(INT4)** 크게 축소하나 정확도 저하 주의(고급기법 필요).
- **Sparsity** — 일부 파라미터를 0으로 설정해 불필요 연산 건너뜀. **2:4 sparsity**(4개 중 2개를 0)는 전용 HW 가속.

## 2. LLM 진화 & 추론

- LLM = transformer + self-attention, 수백억 파라미터. **Inference**(추론) = 학습된 지식으로 실시간 출력.
- 토큰 단위 처리(문자/서브워드/단어). 비전 모델은 픽셀→임베딩. **MoE(Mixture of Experts)** = 일부만 활성화해 컴퓨트 절감.

## 3. 추론 서빙의 과제

- 수십억 파라미터 → GPU 메모리 대량 필요(가중치 + KV cache). 동시요청·긴 입력 증가 시 메모리 병목.
- 기본 서빙은 비효율 배칭 → HW 저활용·지연. attention 연산 집약 → 긴 입력 시 느림.
- 해법: 효율 메모리관리, 고급 배칭, paged attention.

## 4. 풀스택 추론 성능 접근

- 추론은 상시 발생 → 학습보다 더 비싸질 수 있음. 비용 최적화 = 메모리↓·throughput↑·트래픽 라우팅·HW↓ (정확도 희생 없이).
- 모델 최적화(양자화·sparsity) + 서빙 런타임 최적화(chunked prefill, prefix caching, speculative decoding, disaggregated prefill/decode).

### 추론 런타임 비교
| 런타임 | 특징 |
|---|---|
| **vLLM** | OSS 커뮤니티 유지, paged attention, 고처리량·저지연, 폭넓은 채택 |
| **Triton** | 독립 런타임 아님, 백엔드(TensorRT·vLLM) 프런트엔드 API. NVIDIA서 약간 빠를 수 있으나 셋업 복잡·모델 지원 제한 |
| **SGLang** | vLLM 파생, 특정 유스케이스 최적화. 모델 아키텍처 지원 적음, 커뮤니티 작음 |

## 5. 이중 효율화 접근

### (1) 런타임 최적화 = vLLM
- **Continuous batching**(GPU 유휴↓), **PagedAttention**(KV cache 효율, 동시요청·긴 시퀀스).
- HF에서 직접 모델 로드, Triton 백엔드로도. NVIDIA·AMD GPU·Google TPU 호환. 표준화로 벤더 종속 회피.

### (2) 모델 최적화 = 압축
- 양자화: FP16→INT8/INT4. **Llama 70B ≈ 140GB → 40GB**. 48GB VRAM GPU가 40GB 모델을 140GB보다 빠르게.
- fine-grained 양자화(스케일링 팩터)로 **정확도 저하 1% 미만**, 처리량 2배.
- Sparsity: 가중치 0화. 재학습 필요(상당한 선행자원), HW 의존. 보통 **양자화를 1차 권장**.
- 정확도: 8-bit 거의 베이스라인, 4-bit도 고급기법(weight rounding·calibration)으로 강한 성능, 2:4 sparsity 품질 유지.

## 6. Red Hat AI로 추론 최적화

- **Red Hat AI** = 하이브리드 클라우드 AI 가속 플랫폼. 포함:
  - 최적화·검증 모델 / **LLM Compressor**(양자화·압축, **99% 정확도 유지** 목표) / 고성능 vLLM 런타임 / **llm-d 분산추론**(fleet-wide 오케스트레이션) / LLMOps / AI 안전·평가 / 유연한 스케일 / 에이전트 가속.
- 검증 툴: **GuideLLM, lm-evaluation-harness, vLLM**으로 벤치마크 → 재현성·정보기반 모델 선택. **capacity 가이드**로 인프라 계획.

## 메모

- 추론 입문에 최적. "왜 압축하나/정확도 괜찮나"가 명확. 09([[09-프로덕션환경-구축-고려사항]])의 추론 섹션과 보완.
- 관련 vault: [[01-RHOAI-기초-용어정리]].
