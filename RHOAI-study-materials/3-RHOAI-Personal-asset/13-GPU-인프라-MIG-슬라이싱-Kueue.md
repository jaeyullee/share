---
title: GPU 인프라 운영 - MIG, 동적 슬라이싱, Kueue, RDMA
date: 2026-04-10
tags: [ai, study, gpu, mig, kueue, rdma, openshift-ai, ocp]
---

# GPU 인프라 운영: OCP 엔지니어가 알아야 할 것들

> MIG 슬라이싱, 동적 할당, Kueue 스케줄링, RDMA 가속까지. OCP 운영 관점 10분 요약.

---

## 1. GPU 할당 문제: 왜 MIG가 필요한가

**비유: 회의실 예약 시스템**

기본 Kubernetes에서 GPU는 회의실 하나를 통째로 예약하는 방식이다. 5명짜리 미팅에 100인 강당을 잡는 것과 같다. 나머지 95석은 그냥 비어 있다.

MIG(Multi-Instance GPU)는 강당을 칸막이로 나눠 여러 팀이 동시에 쓰게 한다. NVIDIA A100 하나를 최대 7개 독립 인스턴스로 분할할 수 있다.

**MIG 프로파일 예시 (A100 40GB 기준)**

| 프로파일 | 인스턴스 수 | 메모리 | 적합한 워크로드 |
|---------|------------|--------|----------------|
| `1g.5gb` | 최대 7개 | 5GB | 소형 추론, 개발/테스트 |
| `2g.10gb` | 최대 3개 | 10GB | 중소형 모델 |
| `3g.20gb` | 최대 2개 | 20GB | 중형 모델 (7B급) |
| `7g.40gb` | 1개 | 40GB | 대형 단일 워크로드 |

각 인스턴스는 메모리, 캐시, 컴퓨팅 코어가 격리되어 있어 테넌트 간 간섭이 없다.

---

## 2. 정적 MIG vs 동적 슬라이싱

**정적 MIG의 문제**

미리 슬라이스를 잘라두면 실제 수요와 안 맞는 경우가 생긴다. `3g.20gb` 슬라이스가 남아 있어도 `1g.5gb`를 요청한 Pod는 Pending 상태로 대기한다. 타입 불일치 때문에 GPU 여유가 있어도 못 쓰는 상황이다.

**동적 슬라이싱 (DAS Operator)**

Pod가 GPU를 요청하는 순간에 슬라이스를 생성하고, Pod가 종료되면 자동으로 회수한다.

```
Pod 요청 → Scheduling Gate로 대기
         → DAS Operator가 MIG 슬라이스 생성
         → 슬라이스 연결 후 Pod 시작
         → Pod 종료 → 슬라이스 자동 삭제
```

**설치 순서 (OpenShift 웹 콘솔 기준)**

1. cert-manager 설치
2. NVIDIA GPU Operator 설치
3. Node Feature Discovery 설치
4. Dynamic Accelerator Slicer Operator 설치
5. DASOperator 인스턴스 생성 (기본 설정)

**Pod 스펙 예시**

```yaml
resources:
  limits:
    nvidia.com/mig-1g.5gb: 1   # 소형 7개 배치
    # 또는
    nvidia.com/mig-3g.20gb: 1  # 중형 2개 배치
    # 또는
    nvidia.com/mig-7g.40gb: 1  # 전체 GPU급 1개
```

사용자는 리소스 요청만 선언하면 된다. 슬라이스 생성/삭제는 플랫폼이 처리한다.

---

## 3. MIG 혼합 전략과 MIG Adapter

**혼합 전략(Mixed Strategy)의 현실적 문제**

A100은 19가지 혼합 구성을 지원한다. 다양한 크기를 섞어 쓰면 활용률이 높아지지만, Kubernetes에서는 MIG 타입별로 다른 리소스 타입으로 등록된다. `1g.5gb`가 없으면 `3g.20gb`가 남아 있어도 Pod는 Pending이다.

**MIG Adapter: 빌려 쓰기**

MIG Adapter는 Pending Pod를 감시하다가, 요청한 타입이 없으면 상위 호환 타입으로 자동 업그레이드해 배치한다.

```
호환 체인 (A100):
1g.5gb → 2g.10gb → 3g.20gb → 4g.20gb

Pod가 1g.5gb 요청 → 없음 → 2g.10gb로 배치
나중에 1g.5gb가 생기면 → 원래 크기로 복원
```

Mutating Admission Webhook으로 Pod 스펙을 패치하는 방식이라 Pod 재배포 없이 동작한다.

---

## 4. GPU 스케줄링: Kueue

**비유: 은행 번호표 시스템**

기본 Kubernetes ResourceQuota는 창구 수를 제한하지만, 대기열 관리는 못 한다. 창구가 꽉 차면 그냥 거절이다. Kueue는 번호표를 뽑고 순서대로 처리하는 시스템이다.

**Kueue 핵심 개념**

| 개념 | 역할 | 비유 |
|------|------|------|
| ClusterQueue | 전체 GPU 풀 관리 | 은행 전체 창구 |
| LocalQueue | 팀/네임스페이스별 큐 | 팀별 번호표 발급기 |
| ResourceFlavor | GPU 타입 구분 | 창구 종류 (일반/VIP) |
| Cohort | 자원 공유 그룹 | 같은 층 부서들 |

**Quota Borrowing: 유휴 GPU 최소화**

같은 Cohort 내에서 남는 quota를 다른 팀이 임시로 빌려 쓸 수 있다. 원래 팀이 필요하면 즉시 반환한다.

IBM Vela 사례:
- 팀별 명목 quota 22%, 예비 10%
- Borrowing 없으면 약 30% GPU가 idle
- Borrowing 적용 후 idle GPU 1% 미만

**Gang Scheduling**

분산 학습은 GPU 여러 개가 동시에 필요하다. 일부만 뜨면 나머지가 자원을 점유한 채 대기한다. Kueue의 gang scheduling은 필요한 GPU를 모두 확보할 수 있을 때만 Pod를 생성한다.

**Suspend/Resume**

낮은 우선순위 작업은 종료가 아니라 suspend 후 재큐잉된다. 체크포인팅과 함께 쓰면 작업 진행 상태를 보존하면서 자원을 반납할 수 있다.

---

## 5. Kueue + KEDA: Scale-to-Zero

**문제**: 추론 서비스가 트래픽 없을 때도 GPU를 점유한다.

**해결**: KEDA가 GPU 사용률 메트릭을 감시하다가 0이 되면 워크로드를 0으로 축소한다. Kueue가 반납된 GPU를 대기 중인 다음 작업에 자동 배정한다.

```
흐름:
GPU 사용률 0 지속 → KEDA가 워크로드 scale-to-zero
                  → Kueue가 GPU quota 반납 감지
                  → 대기 중인 다음 workload admit
                  → GPU 재할당
```

**ScaledObject 핵심 설정**

```yaml
triggers:
- type: prometheus
  metadata:
    query: sum(rate(DCGM_FI_DEV_GPU_UTIL{pod=~"my-raycluster.*"}[1m]))
    threshold: "1"
pollingInterval: 30
cooldownPeriod: 300
```

KEDA는 0↔1 스케일링이 가능하다. 일반 HPA는 최소 1개를 유지해야 해서 완전한 GPU 반납이 안 된다.

---

## 6. GPUDirect RDMA: 분산 학습 가속

**비유: 택배 경로 단축**

기본 분산 학습에서 GPU 간 데이터는 GPU 메모리 → CPU 메모리 → 네트워크 → CPU 메모리 → GPU 메모리 경로를 거친다. 택배가 물류센터를 두 번 거치는 것과 같다.

GPUDirect RDMA는 GPU 메모리에서 네트워크로 직접 전송한다. 중간 CPU 경유를 없앤다.

**성능 비교 (Llama 3.1 8B, FSDP 미세조정)**

| 네트워크 구성 | 학습 시간 |
|-------------|---------|
| 기본 OVN-Kubernetes | 5시간 |
| Spectrum-4 보조 인터페이스 + TCP | 2시간 30분 |
| GPUDirect RDMA (RoCE) | 1시간 40분 |

기본 OVN 대비 약 3배 단축. 통신 병목이 사라지면 IO-bound에서 compute-bound로 전환되고, Flash Attention 같은 커널 최적화 효과도 더 잘 드러난다.

**OpenShift AI 설정 핵심 구성 요소**

| 구성 요소 | 역할 |
|----------|------|
| NVIDIA Network Operator | NIC 드라이버, RDMA device plugin |
| NVIDIA GPU Operator | GPU 드라이버, GPUDirect RDMA 활성화 |
| SR-IOV Operator | NIC를 virtual function으로 Pod에 부착 |
| Multus CNI | Pod에 보조 네트워크 인터페이스 추가 |
| NCCL | GPU 간 집단 통신 최적화 |

**ClusterPolicy에서 RDMA 활성화**

```yaml
spec:
  driver:
    rdma:
      enabled: true
```

**PyTorchJob에서 RDMA 사용 설정**

```yaml
# Pod annotation
k8s.v1.cni.cncf.io/networks: "rdmashared-net"

# 환경 변수
NCCL_SOCKET_IFNAME: net1

# 리소스 요청
resources:
  limits:
    rdma/rdma_shared_device_eth: "1"
```

**주의**: CRI-O에서 non-root RDMA를 위해 memlock 한도를 늘려야 한다. MachineConfig로 worker 노드에 `default_ulimits = ["memlock=-1:-1"]` 적용 후 재시작 필요.

---

## 7. GPU Operator 생태계 구성 요소 한눈에 보기

OCP에서 GPU를 쓰려면 여러 Operator가 협력한다. 처음 보면 복잡해 보이지만 역할이 명확하다.

| Operator/컴포넌트 | 역할 | 없으면? |
|-----------------|------|---------|
| NFD (Node Feature Discovery) | 노드 하드웨어 감지, 레이블 부착 | GPU Operator가 GPU 노드를 못 찾음 |
| NVIDIA GPU Operator | 드라이버, device plugin, toolkit 자동 배포 | Pod에서 GPU 사용 불가 |
| KMM (Kernel Module Management) | OOT 커널 모듈 빌드/배포/관리 | 커스텀 드라이버 수동 관리 필요 |
| NVIDIA Network Operator | RDMA NIC 드라이버, device plugin | GPUDirect RDMA 사용 불가 |
| DAS Operator | 동적 MIG 슬라이싱 | 정적 MIG만 가능 |
| Kueue | GPU 큐잉, quota 관리 | 선착순 GPU 점유, 유휴 낭비 |

**KMM 특이사항**: Intel GPU(Flex 140) 사용 시 기존 in-tree 드라이버(`i915`)를 blacklist 처리하고 OOT 드라이버를 로드해야 한다. NFD로 Intel GPU 노드를 감지하고, KMM Module CR로 해당 노드에만 드라이버를 배포한다.

---

## 핵심 정리 (4줄 요약)

1. MIG는 GPU를 격리된 인스턴스로 분할한다. 정적 파티셔닝보다 DAS Operator 기반 동적 슬라이싱이 실제 수요에 유연하다.
2. Kueue는 GPU 큐잉과 quota 관리를 담당한다. Cohort borrowing으로 유휴 GPU를 최소화하고, gang scheduling으로 분산 학습 자원 일관성을 보장한다.
3. KEDA + Kueue 조합으로 scale-to-zero와 자동 재할당을 구현한다. IBM Vela는 이 조합으로 90% GPU 활용률을 달성했다.
4. GPUDirect RDMA는 분산 학습 통신 병목을 제거한다. 기본 OVN 대비 3배 학습 시간 단축, IO-bound에서 compute-bound로 전환된다.
