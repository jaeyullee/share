# RHOAI 워커노드 리소스 산정법

> OCP 위 RHOAI 추론 서빙을 위한 워커노드 사이징.
> GPU/VRAM/CPU/RAM/스토리지/네트워크를 **동시에** 만족해야 하며, 보통 **하나가 binding constraint**가 된다.

---

## 산정 공식 (레이어별)

```
호스트 CPU(물리코어) = Σ_pod (2 + N_pod)  +  시스템예약  +  데몬셋
   N_pod = 그 파드가 쓰는 GPU/MIG 슬라이스 수 (= 텐서병렬 TP 차수)
   하이퍼스레딩이면 vCPU = 물리코어 × 2

호스트 RAM ≈ Σ(모델 로딩·토크나이저·CPU offload)  +  시스템  +  데몬셋
   (VRAM과 별개. 흔히 모델 크기의 1.5~2배 권장)

GPU/VRAM = 모델별 (가중치×1.2 + KV) ≤ 슬라이스/카드 메모리
   (계산법 → 01-LLM-필요VRAM-계산법, 프로파일 → 02-MIG-프로파일-선택-계산법)
```

---

## 파드당 CPU = `2 + N` (vLLM 기준)

vLLM 서빙 파드 1개당 최소 호스트 물리코어:

| 프로세스 | 개수 | 역할 |
|---|---|---|
| API 서버 | 1 | HTTP·토크나이즈·입력 처리 |
| 엔진 코어 | 1 | 스케줄러 (busy loop — CPU 굶기면 치명적) |
| GPU 워커 | N | GPU/슬라이스 1개당 1개 (TP 차수) |

- **TP=1** (MIG 슬라이스 1개) → `2+1 = 3코어`
- **TP=4** (모델이 GPU 4장) → `2+4 = 6코어` (파드 1개, N=4)
- replica(HA) 늘리면 → **파드 수 × (2+N)**
- "2+N"은 **파드당**. 노드 위 모든 서빙 파드를 합산.

> CPU가 프로세스 수보다 부족하면 엔진 코어가 굶어 throughput·latency 붕괴.

---

## 레이어별 고려표

| 레이어 | 산정 대상 | 메모 |
|---|---|---|
| ① GPU VRAM | 가중치+KV fit | 1차 제약 |
| ② GPU 컴퓨트 | SM 슬라이스 ↔ TTFT/throughput SLA | MIG 프로파일 결정 |
| ③ 호스트 CPU | Σ(2+N) + 오버헤드 | MIG 밀도 높으면 여기서 막힘 |
| ④ 호스트 RAM | 모델 로딩·KV offload | VRAM과 별개, 1.5~2배 |
| ⑤ 스토리지/풀 | 가중치 다운로드(70B=140GB) | ephemeral-storage, PVC 캐시, 풀 대역폭 |
| ⑥ 네트워크 | 멀티노드 TP/PP, llm-d | RDMA/RoCE, GPUDirect |
| ⑦ NUMA/토폴로지 | GPU-CPU-NIC 동일 NUMA | 어긋나면 PCIe 홉↑ |
| ⑧ 시스템예약+데몬셋 | 노드별 고정 오버헤드 | 아래 참조 |

### ⑧ 시스템 예약 + DaemonSet (OCP 특유, 놓치기 쉬움)
- **kube-reserved / system-reserved**: kubelet·CRI-O·OS (노드당 대략 CPU 1~2코어 + RAM 수 GB)
- **NVIDIA GPU Operator 데몬셋**: device plugin, DCGM exporter, NFD, MIG manager
- **OVN-Kubernetes, Multus, CSI, 모니터링(node-exporter), 로깅**
- → 노드당 대략 **2~4 물리코어 + 수 GB RAM** (환경마다 다름, 실측으로 보정)

---

## MIG 밀도 → CPU 폭증 주의

GPU를 잘게 쪼갤수록 파드 수가 늘어 **호스트 CPU가 폭증**한다.

```
A100 1장 → 1g.5gb ×7 → 7개 모델 TP=1
추론 CPU = 7파드 × 3 = 21 물리코어 (GPU는 1장인데!)
→ GPU가 아니라 호스트 CPU/RAM이 슬라이스 밀도를 제한
```

**GPU 쪼개기와 호스트 자원은 세트로 사이징**해야 한다.

---

## MIG 슬라이스는 누가 소비하나 — baremetal vs VM 노드

MIG는 GPU 내부 하드웨어 분할일 뿐, **슬라이스를 가져가는 주체는 위 계층이 결정**한다.

| 구성 | 슬라이스 소비 주체 | 동적 재분할 |
|---|---|---|
| **베어메탈 노드** | **파드** (device plugin이 광고, 단일노드 멀티파드) | ✅ K8s/GPU Operator로 유연 |
| **VM 노드 ① 풀 패스스루** | 파드 (GPU 통째→VM 1개→VM 안에서 MIG→파드) | ✅ VM 내부에서 유연 |
| **VM 노드 ② MIG-vGPU (mediated)** | **VM(=노드)** (하이퍼바이저가 슬라이스를 VM별 배분) | ❌ VM 경계 고정, 하이퍼바이저가 관리 |

**사이징 함의**:
- 베어메탈/풀패스스루(①) → 노드가 GPU 전체를 보고 MIG 유연 구성. RHOAI 기본 패턴.
- MIG-vGPU(②, OpenShift Virtualization·vSphere vGPU 등) → **OCP 노드(VM)는 vGPU 1개만 보임**, K8s에서 재분할 불가. 슬라이스 배치를 **하이퍼바이저 레벨에서 미리 확정**해야 함. vGPU 소프트웨어·라이선스 필요.

---

## 워크된 노드 예시

**노드: A100 80GB ×4, 풀 GPU로 4개 모델 TP=1 서빙**
```
추론 CPU   = 4파드 × (2+1)          = 12 물리코어
시스템예약 + 데몬셋                  ≈  3~4 물리코어
─────────────────────────────────────────────
최소         ≈ 15~16 물리코어  → HT면 약 32 vCPU
권장(헤드룸)  ≈ 24~32 물리코어 노드
RAM         ≈ VRAM(320GB) 대응 + 로딩 여유 → 512GB+
```

**같은 노드를 MIG 7-way로 28개 모델 시도**
```
추론 CPU = 28파드 × 3 = 84 물리코어 (!!)
→ GPU(4장)는 남는데 CPU 폭발 → CPU/RAM이 슬라이스 밀도 제한
```

---

## 산정 순서 (권장)

1. **모델별 VRAM fit** → MIG 프로파일/카드 결정 (①②)
2. **노드당 슬라이스/파드 수** 확정
3. **Σ(2+N) + 시스템 오버헤드** → 호스트 CPU (③⑧)
4. **RAM·스토리지·네트워크** 교차 검증 (④⑤⑥)
5. **NUMA 정렬 + replica/HA 헤드룸** 반영 (⑦)
6. 가장 빡빡한 레이어 = binding constraint → 거기 맞춰 노드 스펙 확정

> 정확한 reserve 수치·RHOAI 권장 노드 스펙은 **Red Hat OpenShift AI Sizing/Reference Architecture**에 버전별로 명시. 제안서엔 그 숫자를 인용하고, reserve는 고객 클러스터 실측(`oc describe node`의 Allocatable)으로 보정.

---

## 관련 노트

- 필요 VRAM 계산: `01-LLM-필요VRAM-계산법.md`
- MIG 프로파일 선택: `02-MIG-프로파일-선택-계산법.md`
