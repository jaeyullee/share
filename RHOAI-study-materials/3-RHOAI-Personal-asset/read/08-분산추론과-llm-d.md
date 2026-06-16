---
title: 분산 추론과 llm-d (OCP 엔지니어 관점)
date: 2026-04-10
tags:
  - ai
  - study
  - inference
  - distributed
  - llm-d
  - moe
---

# 분산 추론과 llm-d (OCP 엔지니어 관점)

> 단일 GPU에 모델이 안 들어갈 때, 또는 수백 개 요청을 동시에 처리해야 할 때 어떻게 확장하는가. OCP 클러스터 운영 경험으로 분산 추론을 이해한다.

---

## 1. 왜 분산 추론이 필요한가

**문제**: LLM은 크다. Llama 70B는 FP16 기준 약 140GB, DeepSeek-R1은 약 720GB다. A100 80GB GPU 한 장에 안 들어간다.

**해결**: 모델을 여러 GPU에 나눠 올린다.

| 상황 | 해결책 |
|------|--------|
| 모델이 GPU 1장에 안 들어감 | 텐서 병렬화 (TP) |
| 노드 하나로도 부족한 초대형 모델 | 파이프라인 병렬화 (PP) |
| 처리량을 선형으로 늘리고 싶음 | 데이터 병렬화 (DP, 복제본 추가) |
| MoE 모델의 전문가를 분산 | 전문가 병렬화 (EP) |

**OCP 비유**: TP는 하나의 Pod을 여러 노드에 쪼개는 것, DP는 같은 Deployment의 복제본을 늘리는 것이다.

---

## 2. 텐서 병렬화 (Tensor Parallelism)

모델의 가중치 행렬을 GPU 여러 장에 분산해 동시에 계산한다.

```
GPU 0: 가중치 행렬의 절반 → 부분 결과 계산
GPU 1: 가중치 행렬의 나머지 → 부분 결과 계산
                ↓
        all-reduce로 결과 합산
```

| 항목 | 내용 |
|------|------|
| 장점 | 지연 시간 감소, 메모리 대역폭 확장 |
| 단점 | GPU 간 통신(all-reduce) 오버헤드 |
| 전제 조건 | NVLink 또는 InfiniBand 같은 고대역폭 인터커넥트 |
| 권장 범위 | 노드 내부 GPU 간 (NVLink 활용) |

**실측 (Llama 70B)**:
- TP=1 → TP=2: KV 캐시 블록 923개 → 12,830개 (13.9배)
- 처리량 2,282 tok/s → 8,967 tok/s (3.9배, GPU 2배 대비 초선형)

KV 캐시 공간이 늘어나면서 더 큰 배치를 처리할 수 있어 GPU 수 증가보다 처리량이 더 크게 오른다.

---

## 3. 파이프라인 병렬화 (Pipeline Parallelism)

모델 레이어를 연속 구간으로 나눠 여러 GPU/노드에 배치한다.

```
GPU 0: Layer 0~15 처리 → 중간 활성값 전달
GPU 1: Layer 16~31 처리 → 중간 활성값 전달
GPU 2: Layer 32~47 처리 → 최종 출력
```

| 항목 | 내용 |
|------|------|
| 장점 | 통신 빈도 낮음, 초대형 모델 수용 |
| 단점 | 지연 시간 개선 효과 작음 |
| 적합 | 노드 간 확장 (PCIe/이더넷 환경) |

**원칙**: 노드 내부는 TP, 노드 간은 PP. NVLink/InfiniBand가 충분히 빠르면 노드 간에도 TP 확장 가능.

---

## 4. 분산 학습의 네트워크 병목

분산 학습(FSDP 기반)에서 네트워크가 GPU만큼 중요하다. OpenShift 기본 Pod 네트워크는 멀티노드 학습에서 심각한 병목이 된다.

| 네트워크 구성 | H100 2노드 처리량 | 비고 |
|-------------|-----------------|------|
| Pod network (OVN) | 3.46 samples/s | 단일 노드(21.34)보다 느림 |
| vNIC | 12.28 samples/s | Pod network 대비 3.5배 |
| SR-IOV | 40.36 samples/s | vNIC 대비 3.3배 |
| SR-IOV + RDMA | 40.58 samples/s | SR-IOV와 거의 동일 (8B 모델 기준) |

**핵심 교훈**:
- H100처럼 빠른 GPU는 네트워크가 약하면 멀티노드 확장이 오히려 역효과
- L40S 클러스터에서는 vNIC만으로도 8노드에서 단일 노드 대비 6.2배 처리량
- SR-IOV는 H100 환경에서 사실상 필수

**OpenShift 구현**: Multus + NetworkAttachmentDefinition(NAD)으로 vNIC/SR-IOV 인터페이스를 Pod에 부착한다.

---

## 5. llm-d: Kubernetes 네이티브 분산 추론 오케스트레이터

**llm-d = vLLM 위의 Kubernetes 네이티브 오케스트레이션 계층**

OCP에서 Istio가 서비스 메시를 담당하듯, llm-d는 LLM 추론 요청의 지능형 라우팅과 분산 처리를 담당한다.

### 핵심 아키텍처

```
클라이언트 요청
    ↓
Inference Gateway (kgateway)
    ↓
추론 스케줄러 (KV 캐시 상태 + 부하 + SLO 기반 라우팅)
    ↓
┌─────────────────┬─────────────────┐
│  Prefill Worker │  Decode Worker  │
│  (연산 집약)    │  (메모리 집약)  │
└─────────────────┴─────────────────┘
```

### 일반 로드밸런서 vs llm-d

| 항목 | 일반 로드밸런서 | llm-d |
|------|--------------|-------|
| 라우팅 기준 | 라운드로빈, 연결 수 | KV 캐시 상태 + 부하 + SLO |
| KV 캐시 인식 | 없음 | 있음 (prefix-aware routing) |
| Prefill/Decode 분리 | 없음 | 있음 |
| 비용 절감 | 없음 | 30~50% 절감 보고 |

**OCP 비유**: 일반 Service는 라운드로빈이지만, llm-d는 "이 요청의 시스템 프롬프트가 GPU 0의 KV 캐시에 이미 있으니 GPU 0으로 보낸다"는 스티키 세션보다 훨씬 똑똑한 라우팅이다.

### Prefill/Decode 분리 (PD Disaggregation)

LLM 추론의 두 단계를 다른 GPU 그룹에서 처리한다.

```
비싼 GPU (H100) → Prefill Worker (연산 집약)
저렴한 GPU (A10) → Decode Worker (메모리 집약)
```

효과: GPU 자원을 특성에 맞게 배치해 비용 효율 향상. KV 캐시는 NIXL(NVIDIA Inference Xfer Library)로 Prefill에서 Decode로 전송된다.

---

## 6. MoE 모델과 Wide Expert Parallelism

**MoE(Mixture of Experts)** = 모델 안에 여러 "전문가" 네트워크가 있고, 각 토큰이 top-k 전문가만 선택해 처리하는 구조. DeepSeek-R1은 256개 전문가, 6,710억 파라미터다.

**문제**: 전문가가 수백 개면 일반 텐서 병렬화로는 비효율적이다.

**Wide EP(Expert Parallelism)** = 전문가를 GPU에 분산 배치하고, 토큰이 자신의 전문가가 있는 GPU로만 이동한다.

```
일반 TP: 모든 토큰이 모든 GPU를 거침 (통신 과다)
Wide EP: 토큰이 선택한 전문가 GPU로만 이동 (희소 통신)
```

### dispatch/combine 구현체 비교

| 구현체 | 특성 | 적합 환경 |
|--------|------|---------|
| **DeepEP** | nvshmem 기반, 고처리량/저지연 모드 분리 | 멀티노드, 대규모 |
| **PPLX** | 유연하고 운영 단순, CUDA graph 호환 | 단일 노드, chunked prefill |

### EPLB (Expert Placement with Load Balancing)

특정 전문가에 요청이 몰리는 문제를 해결한다. 자주 선택되는 전문가를 복제하고 주기적으로 배치를 재조정한다.

**OCP 비유**: HPA가 Pod을 복제하듯, EPLB가 인기 전문가를 복제한다.

---

## 7. DeepSeek-R1 최적화: MLA + MTP

DeepSeek-R1은 일반 Llama 계열과 아키텍처가 달라 별도 최적화가 필요하다.

| 기술 | 역할 | 효과 |
|------|------|------|
| **MLA** (Multi-Head Latent Attention) | KV 캐시를 압축된 공간으로 투영 | 최대 토큰 용량 67K → 650K |
| **MTP** (Multi-Token Prediction) | 한 번에 여러 토큰 예측 | 저QPS 환경 최대 20% 속도 향상 |
| **torch.compile** | 모델 자동 최적화 | 48% 속도 향상 (차트 기준) |

**성능 개선 타임라인**:
- v0.7.1: MLA 도입 (3x TP 기준)
- v0.7.2: torch.compile 도입 (+48%)
- v0.7.3: MTP 도입 (+69% 누적)

---

## 8. vLLM Semantic Router: 토큰 비용 최적화

모든 요청을 비싼 클라우드 모델로 보내지 않고, 요청 난이도에 따라 라우팅한다.

```
"프랑스 수도는?" → 로컬 모델 (무료)
"귀납법으로 증명하라" → 클라우드 고성능 모델 (유료)
```

**Athena 0.2 릴리스 주요 기능**:
- mmBERT-32K 기반 8개 신경망 분류기 (의도, 탈옥 감지, PII 등)
- HNSW 시맨틱 캐시 (의역된 중복 요청도 캐시 히트)
- 라우팅 지연: P50 40ms, P99 93ms (LLM 추론 800~11,000ms 대비 무시 가능)

**실측 결과**: 21개 프롬프트 테스트에서 86%가 로컬 처리, 14%만 클라우드 사용. 토큰 비용 90% 이상 절감 가능.

---

## 핵심 요약 (3줄)

1. 분산 추론은 TP(지연 감소) + PP(초대형 모델 수용) + DP(처리량 확장) 조합이며, 네트워크 품질이 GPU만큼 중요하다.
2. llm-d는 KV 캐시 인식 라우팅과 Prefill/Decode 분리로 vLLM 클러스터를 지능적으로 오케스트레이션한다.
3. MoE 모델(DeepSeek 계열)은 Wide EP + EPLB로 수백 개 전문가를 멀티노드에 효율적으로 분산한다.
