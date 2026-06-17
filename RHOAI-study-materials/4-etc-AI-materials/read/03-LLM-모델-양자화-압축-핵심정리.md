---
title: LLM 모델 양자화·압축 핵심정리
date: 2026-04-10
tags: [ai, study, llm, quantization, compression, models, vllm]
---

# LLM 모델 양자화·압축 핵심정리

> OCP 엔지니어 관점 | 10분 분량

---

## 왜 양자화를 알아야 하나

OpenShift AI에서 LLM을 서빙할 때 가장 먼저 부딪히는 벽은 **GPU 메모리**다. Llama 3.1 70B를 FP16으로 올리면 약 140GB VRAM이 필요하다. A100 80GB 두 장도 모자란다.

양자화는 이 문제를 해결하는 핵심 기법이다. 모델 가중치를 낮은 비트로 표현해 메모리를 줄이고, 추론 속도를 높인다. Red Hat이 50만 건 이상 평가한 결과, 제대로 적용하면 **정확도 손실은 1% 미만**이다.

---

## 모델 이름 읽는 법

모델 이름은 암호처럼 보이지만 규칙이 있다.

```
meta-llama/Llama-3.1-70B-Instruct-FP8
  브랜드   버전  크기  목적    양자화
```

| 표기 | 의미 |
|------|------|
| `8B`, `70B`, `405B` | 파라미터 수 (GPU 메모리 직결) |
| `Base` | 사전학습 기반 모델, 파인튜닝 출발점 |
| `Instruct` | 지시 따르기 최적화, 채팅용 |
| `Vision` | 텍스트+이미지 멀티모달 |
| `FP8`, `INT8`, `W4A16` | 양자화 방식 |
| `MoE` | 혼합 전문가 아키텍처 |
| `distill` | 큰 모델로 작은 모델을 학습시킨 증류 모델 |

---

## 양자화 방식 비교

비유하자면, 원본 FP16 모델은 **4K 화질 영상**이다. 양자화는 화질을 낮추되 내용은 유지하는 압축이다.

| 방식 | 압축률 | 속도 향상 | 적합 환경 | 정확도 복구 |
|------|--------|-----------|-----------|-------------|
| **W8A8-INT** | ~2배 | ~1.8배 | 서버, 처리량 중심 | 99%+ |
| **W8A8-FP** | ~2배 | ~1.8배 | Hopper/Ada GPU | 99%+ |
| **W4A16-INT** | ~3.5배 | ~2.4배 | 엣지, 지연 민감 | 98%+ |

- **W8A8**: 가중치(W)와 활성값(A) 모두 8비트. 고부하 환경에서 진가를 발휘한다.
- **W4A16**: 가중치만 4비트. 저부하에서 지연시간을 줄이는 데 유리하다.

> **핵심**: 큰 모델(70B, 405B)일수록 양자화 효과가 크고 정확도 손실이 작다. 8B 모델은 다소 변동성이 있지만 의미는 유지된다.

---

## LLM Compressor: 압축 도구의 통합

기존에는 AutoGPTQ, AutoAWQ, AutoFP8 등 도구가 제각각이었다. **LLM Compressor**는 이를 하나로 통합한 Red Hat/Neural Magic의 오픈소스 라이브러리다.

```bash
pip install llmcompressor
```

### 핵심 알고리즘

| 알고리즘            | 역할                     |
| --------------- | ---------------------- |
| **GPTQ**        | 후처리 양자화, 정밀도 보존        |
| **SmoothQuant** | 활성화 분포를 완화해 양자화 용이하게   |
| **SparseGPT**   | 2:4 희소화 (50% sparsity) |

### 실제 성능 (Llama 3.1 70B, A100)

- W8A8 양자화 모델 2장 = 비양자화 FP16 모델 4장과 유사한 지연 성능
- **절반의 GPU로 동일한 SLA** 달성 가능

---

## 멀티모달 양자화

LLM Compressor 0.4.0부터 비전·오디오 모델도 지원한다.

| 모델                   | 벤치마크            | 정확도 복구율      |
| -------------------- | --------------- | ------------ |
| Llama 3.2 Vision 11B | MMMU            | 101.6~105.6% |
| Llama 3.2 Vision 90B | MMMU            | 94.9~101.7%  |
| Whisper Large V2     | LibriSpeech WER | 99.0%        |

트레이싱(Tracing) 기법으로 복잡한 비전·오디오 아키텍처의 계산 그래프를 캡처해 순차 양자화를 적용한다.

---

## Llama 4: MoE + 멀티모달의 결합

Llama 4는 **혼합 전문가(MoE)** 아키텍처를 채택했다. 전체 파라미터 중 일부 전문가만 활성화해 계산 효율을 높인다.

```
Llama 4 Maverick
  총 파라미터: 4천억
  활성 파라미터: 170억 (토큰당)
  전문가 수: 128개
  → 단일 8xH100 노드에서 FP8 버전 구동 가능
```

OCP 관점에서 중요한 점: vLLM이 **출시 당일(Day 0)** 지원을 제공했다. Red Hat이 CUTLASS 기반 GroupedGEMM 커널을 추가해 FP8 추론 성능을 최적화했다.

---

## DeepSeek-R1: 강화 학습으로 만든 추론 모델

DeepSeek-R1은 대규모 지도학습 대신 **강화 학습(RL)** 을 중심에 뒀다.

### 학습 흐름

```
DeepSeek-V3-Base
  → cold-start 데이터 (수천 건)
  → 추론 집약 과제에 GRPO 적용
  → rejection sampling으로 좋은 예시 선별
  → 일반 태스크 확장 + 추가 파인튜닝
  → DeepSeek-R1 완성
```

**GRPO(Group Relative Policy Optimization)**: 기존 RLHF보다 비용을 줄이면서 추론 중심 학습을 수행하는 알고리즘이다.

**Chain of Thought(CoT)**: 모델이 단계적으로 생각할수록 보상을 더 받는다. "aha moment"처럼 스스로 오류를 감지하고 재추론하는 현상이 나타난다.

---

## Granite + InstructLab: Red Hat 생태계 모델

| 도구 | 역할 |
|------|------|
| **Granite** | IBM/Red Hat 오픈소스 LLM, Apache 2.0 |
| **InstructLab** | 파인튜닝 + 커뮤니티 기여 프레임워크 |
| **Ollama** | 로컬 모델 서빙, REST API 제공 |
| **Continue** | VS Code/JetBrains AI 코딩 확장 |

Granite 코드 모델은 116개 프로그래밍 언어로 학습됐고, Docker Hub/Quay.io에서 OCI 이미지로 바로 받을 수 있다. 로컬 노트북에서 GPU 없이도 추론이 가능하다.

---

## KV 캐시 압축 — 가중치 양자화와 다른 축

지금까지는 **모델 가중치(W)** 를 줄이는 양자화였다. 이와 별개로 추론 런타임에 쌓이는 **KV 캐시**를 압축하는 축이 있다. 장문맥일수록 KV 캐시가 GB 단위로 GPU 메모리를 잡아먹기 때문에(크기 ∝ 문맥길이 × KV heads × hidden dim), 가중치 양자화와 독립적으로 메모리를 아낄 수 있다.

- **vLLM**: KV 캐시를 압축하지 않고 PagedAttention(OS 가상메모리식 고정블록 관리)으로 효율적으로 다룸 → **속도 우선**.
- **TurboQuant**: KV 캐시를 4-bit **Vector Quantization**(미리 만든 코드북의 최근접 벡터로 대체, random orthogonal rotation으로 양자화 오류 분산, 학습 불필요·ICLR 2026)으로 압축 → **메모리 우선**(16-bit→4-bit 이론상 ~3.8배 절약).

### 트레이드오프 (벤치마크)

- **속도**: vLLM이 ~5.9배 빠름(247 vs 42 tok/s). TurboQuant은 HF `generate()` 위 Python 오버헤드 + 토큰마다 rotation·codebook lookup으로 FP16 대비 약 -35% 저하.
- **메모리**: TurboQuant이 ~11.5배 적게 사용(6.7GB vs 76.8GB / 80GB GPU).
- **품질**: 둘 다 FP16과 사실상 동일(비교 포인트 아님).
- ⚠️ 위 수치는 **80GB GPU + 3B 모델 + 256토큰**이라 메모리가 넉넉해 TurboQuant에 불리한 조건이다. TurboQuant의 진가는 **VRAM 제한 + 장문맥**에서 나온다. 압축/해제 연산은 공짜가 아니므로 용도에 맞게 선택한다.

> 원본: [[98-Wiki-Raws/etc/TurboQuant_vs_vLLM_Benchmark_Report.pdf]] · Wiki [[turboquant-vs-vllm-benchmark]] (2026-04-09). GQA·PagedAttention·RoPE·SwiGLU 등 기반 개념은 [05-vLLM-추론엔진-핵심정리](05-vLLM-추론엔진-핵심정리.md) 참조.

---

## OCP 엔지니어가 기억할 것

1. **양자화 = GPU 비용 절감의 핵심 수단**. 정확도 손실 걱정은 대부분 과장됐다.
2. **LLM Compressor + vLLM 조합**으로 압축부터 서빙까지 파이프라인을 구성할 수 있다.
3. **모델 이름을 읽으면** 하드웨어 요구사항과 사용 사례를 미리 파악할 수 있다.
4. **MoE 모델(Llama 4, Mixtral)** 은 총 파라미터보다 활성 파라미터 기준으로 GPU를 계획해야 한다.
5. **Granite + InstructLab** 은 사내 데이터로 파인튜닝하고 로컬에서 서빙하는 현실적인 경로다.
6. **가중치 양자화(W4A16 등)와 KV 캐시 압축(TurboQuant 등)은 별개 축**이다. 전자는 모델 적재 메모리·속도, 후자는 장문맥 런타임 메모리를 줄인다.
