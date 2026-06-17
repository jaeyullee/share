---
title: Red Hat AI Inference Technical Overview 정리
date: 2026-06-10
tags:
  - ai
  - redhat
  - inference
  - vllm
  - llm-d
source: Red Hat AI Inference Technical Overview.PDF
---

# Red Hat AI Inference — Technical Overview 정리

> 원본: `Red Hat AI Inference Technical Overview.PDF` — vLLM 내부 메커니즘과 추론 병렬화·레퍼런스 아키텍처를 심화로 다루는 기술 덱.
> 상위 맥락: [00-인덱스](00-인덱스.md) / 입문서는 [05-AI-Inference-입문-ebook](05-AI-Inference-입문-ebook.md)

---

## 1. 추론이 가치가 생기는 지점

- "Inference is where the real world value happens" — 사용자가 모델과 상호작용하는 지점.
- 과제: 인프라 비용(상당한 컴퓨트), 운영 복잡성(비표준 접근), 배포 제약(하이브리드 유연성 부족).
- **Red Hat AI Inference Server**: Fast / Cost-effective / Optimized. Any model, any accelerator, any environment. OpenShift AI·RHEL AI에 포함.

## 2. Red Hat = OSS GenAI 추론 리더

- vLLM 전담 HPC 엔지니어링팀, **코어 커미터 7명**.
- ML 엔지니어링팀이 vLLM 최적화 라이브러리 **llm-compressor** 개발.
- ML 리서치팀이 사전최적화 모델 생산. (Neural Magic 인수 기여.)

## 3. 압축으로 본 효과 (Llama 예시)

| 모델 | 포맷 | 크기 | 서빙메모리 | 지연 | 정확도 |
|---|---|---|---|---|---|
| Llama 3.1 8B (Lean) | FP16 | 16GB | ~40GB | Fast | SOTA |
| Llama 3.1 70B (Bulky) | FP16 | 140GB | ~280-300GB | Slow | SOTA |
| Llama 3.1 70B-FP8 (Fit) | FP8 | 70GB | ~120-140GB | Fast | 고정확도 유지, **GPU 50%↓** |

- **HF Red Hat AI 레포**: 검증(현실 시나리오 테스트, GuideLLM·LM Eval Harness)·최적화(LLM Compressor) 모델.
- **사례**: DBMS사 L70B SQL을 W4A16 양자화 → 정확도 99%+ 회복, **GPU 8→2**. JSON 추출 Llama-70B → **GPU 시간 40% 절감**.

## 4. vLLM 핵심 메커니즘

### KV Cache & PagedAttention
- KV(Key-Value) 캐시로 디코딩 중 attention 상태 저장·재사용 → 중복 계산 제거.
- **PagedAttention**: KV 메모리를 고정 크기 페이지로 할당·재매핑 → 단편화 방지, **32K+ 토큰** 컨텍스트, GPU OOM 회피. continuous batching의 백본.

### Continuous Batching
- 정적/동기 배칭의 비효율 극복. 요청 도착 즉시 동적 배치 구성 → GPU 활용 극대화, 저지연. (S1~S16 슬롯 예시로 naive vs continuous 비교.)

### Speculative Decoding
- 경량 draft 모델이 토큰 후보를 병렬 예측, 최종 모델이 검증. 정확도 유지하며 **토큰당 생성시간 2~3배 단축**.
- 방법군: Medusa, HASS, EAGLE/EAGLE-2/EAGLE-3 (최대 5.6x speedup 그래프).

### 병렬화 기법 (대형 모델 분산)
| 기법 | 분할 대상 | 특징 |
|---|---|---|
| **Tensor Parallelism** | 가중치 행렬을 GPU 분산 | per-device 메모리↓, all-reduce 통신 |
| **Pipeline Parallelism** | 레이어를 디바이스별 | point-to-point, 지연 감소X, 스테이지 불균형 |
| **Expert Parallelism** | 전문가(MoE)를 디바이스별 | all-to-all, TP보다 통신↓ |
| **Data Parallelism** | 입력 분할, 가중치 복제 | 통신↓, 메모리 소비↑ |
| **Disaggregated Serving** | "시간" 차원 분할(prefill/decode 분리) | 지연 제어↑, KV 전송 오버헤드 |
- vLLM은 **혼합 병렬** 지원(TP+PP 예: Llama 3 405B / DP+EP 예: DeepSeek V3). V1 아키텍처: Scheduler→Broadcast→Workers.

## 5. 레퍼런스 아키텍처

1. **Single-Node Inference on RHEL** (Dev/Test) — 단일 RHEL에 vLLM, 외부 의존성 없음(air-gapped 적합), 빠른 피드백 루프.
2. **Hybrid Cloud Model Serving (Edge & Cloud)** — 엣지에 draft 모델(speculative prefill, 양자화/LoRA), 클라우드 최종 모델이 검증. **KV cache 공유**로 중복 제거. Red Hat AI(with llm-d): Inference Gateway → prefill·scheduler·decode·vLLM.
   - 가능 기술: Speculative Decoding, **Disaggregated Prefill**(엣지서 prefill, 중간상태 클라우드 전송), KV Cache Transfer with Decode Split. 응답시간 최대 3배 개선.
   - 유스케이스: Telco 엣지(5G), 프라이버시 워크로드, 리테일/매장 키오스크.
3. **GPU Pooling in Private Cloud** — OpenShift AI로 클러스터 GPU 풀링(GPUaaS). 네임스페이스/팀 공유, 단편화·유휴 제거, RBAC·컨테이너 격리로 멀티테넌트.

## 키 용어

KV cache, PagedAttention, continuous batching, speculative decoding(draft/verification), tensor/pipeline/expert/data parallelism, disaggregated serving, prefill/decode split, GPUaaS, Inference Gateway.

## 메모

- 03은 **vLLM 내부 동작**과 **병렬화/엣지 아키텍처**가 강점. 04(PPTX)는 같은 추론 주제를 영업 수치 중심으로.
- 데모: red.ht/llm_d_vLLm_demo_OpenShiftAI.
- 관련 vault 노트: [04-GPU-인프라-MIG-슬라이싱-Kueue](../3-RHOAI-Personal-materials/04-GPU-인프라-MIG-슬라이싱-Kueue.md), [02-OpenShift-AI-플랫폼-아키텍처](../3-RHOAI-Personal-materials/02-OpenShift-AI-플랫폼-아키텍처.md).
