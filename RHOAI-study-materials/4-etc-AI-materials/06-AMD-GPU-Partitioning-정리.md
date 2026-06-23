# AMD GPU Partitioning 정리

> 목적: AMD Instinct GPU의 partitioning 개념을 NVIDIA MIG/MPS와 비교해 이해한다.  
> 기준: 추론 워크로드, Kubernetes/OpenShift GPU 스케줄링 관점.

---

## 1. 한 줄 요약

AMD GPU partitioning은 **한 GPU를 여러 워크로드가 나눠 쓰기 위한 하드웨어/토폴로지 기반 분할 기능**이다.  
목적은 NVIDIA MIG와 비슷하지만, NVIDIA처럼 `1g.10gb` 같은 고정 GPU 인스턴스를 만드는 방식과는 다르다.

AMD는 주로 아래 두 축을 조합한다.

| 축 | 예시 | 의미 |
|---|---|---|
| Compute partition | `SPX`, `DPX`, `QPX`, `CPX` | compute 실행 도메인을 몇 개로 나눌지 |
| Memory partition | `NPS1`, `NPS4`, `NPS8` | HBM 메모리 NUMA/locality 도메인을 어떻게 나눌지 |

즉 AMD partitioning은 **compute와 memory를 독립 축으로 설정하는 구조**다.

---

## 2. MPS, MIG, AMD Partitioning 차이

| 기능 | 성격 | 핵심 |
|---|---|---|
| NVIDIA MPS | 공유 실행 | 여러 CUDA 프로세스가 한 GPU를 더 효율적으로 공유 |
| Time-slicing | 시간 분할 공유 | GPU를 시간 단위로 번갈아 사용 |
| NVIDIA MIG | 하드웨어 인스턴스 분할 | 한 GPU를 여러 개의 작은 GPU처럼 노출 |
| AMD Instinct partitioning | compute/memory 토폴로지 분할 | compute partition과 memory partition 모드를 조합 |

중요한 구분:

- **MPS/time-slicing**: 한 GPU를 공유한다.
- **MIG/AMD partitioning**: GPU 내부 자원을 더 물리적인 단위로 나눈다.
- **AMD partitioning은 MPS보다는 MIG 쪽에 가깝다.**
- 단, AMD가 NVIDIA MIG와 동일한 UX를 제공한다는 뜻은 아니다.

---

## 3. NVIDIA MIG와의 차이

NVIDIA MIG는 데이터센터 GPU에서 미리 정의된 인스턴스 프로파일을 만든다.

예시:

```text
1g.10gb
2g.20gb
3g.40gb
```

이런 프로파일은 Kubernetes에서 별도 리소스처럼 스케줄링할 수 있다.

```text
nvidia.com/mig-1g.10gb
nvidia.com/mig-2g.20gb
```

AMD는 이와 다르게, GPU 내부의 **compute partition mode**와 **memory partition mode**를 선택한다.

예시:

```text
SPX + NPS1
CPX + NPS4
```

정확한 차이는 다음과 같다.

| 항목 | NVIDIA MIG | AMD Instinct partitioning |
|---|---|---|
| 분할 모델 | 작은 GPU 인스턴스 생성 | compute/memory partition mode 선택 |
| 사용자 경험 | `1g.10gb` 같은 인스턴스 프로파일 | `CPX + NPS4` 같은 토폴로지 프로파일 |
| 분할 단위 | GPU instance profile | XCD, NUMA/locality domain |
| 대표 대상 | A100, H100, H200 등 | MI300X 등 AMD Instinct 계열 |
| 소비자 GPU | RTX 3090/4090/5060 Ti는 MIG 미지원 | RX 9060 XT/7900 XTX는 서버급 partitioning 대상 아님 |

---

## 4. Compute Partition: SPX, DPX, QPX, CPX

MI300X 기준으로 이해하면 쉽다. MI300X는 내부에 여러 XCD가 있고, compute partition mode는 이 XCD들을 몇 개의 실행 도메인으로 보일지 결정한다.

| 모드 | Compute partition 수 | 의미 |
|---|---:|---|
| `SPX` | 1개 | 전체 GPU를 하나의 compute 도메인으로 사용 |
| `DPX` | 2개 | compute를 2개 partition으로 분할 |
| `QPX` | 4개 | compute를 4개 partition으로 분할 |
| `CPX` | 8개 | compute를 8개 partition으로 분할 |

따라서 **CPX는 MI300X 기준 compute를 8개로 나누는 모드**다.  
다만 CPX만 설정한다고 메모리까지 8등분된다는 뜻은 아니다. 메모리 분할은 `NPS` 모드가 따로 결정한다.

---

## 5. Memory Partition: NPS1, NPS4, NPS8

NPS는 메모리 NUMA/locality 구성을 다루는 축이다.

| 모드 | 의미 |
|---|---|
| `NPS1` | 메모리를 하나의 큰 NUMA 도메인처럼 사용 |
| `NPS4` | 메모리 locality를 4개 도메인으로 분할 |
| `NPS8` | 메모리 locality를 8개 도메인으로 분할 |

메모리 partition은 단순히 "VRAM을 몇 GB씩 잘라서 나눠준다"는 의미만은 아니다.  
핵심은 워크로드가 어느 메모리 도메인에 가까운 compute partition에서 실행되는지, 즉 **locality와 bandwidth 경쟁을 어떻게 줄일지**다.

---

## 6. 조합별 이해

compute와 memory는 독립 축이므로 조합에 따라 성격이 달라진다.

| 조합 | Compute | Memory | 해석 |
|---|---|---|---|
| `SPX + NPS1` | 1개 | 1개 | GPU 전체를 하나로 사용 |
| `CPX + NPS1` | 8개 | 1개 | compute는 나뉘지만 memory는 큰 도메인으로 남음 |
| `SPX + NPS4` | 1개 | 4개 | compute는 하나지만 memory locality는 나뉨 |
| `CPX + NPS4` | 8개 | 4개 | compute와 memory locality를 모두 나눠 여러 워크로드에 적합 |

질문으로 자주 헷갈리는 지점:

> compute만 나누면 선택하지 않은 memory는 공유되는가?

대체로 맞다. 더 정확히는 **memory가 단일 또는 더 큰 NUMA 도메인으로 남아 partition 간 locality/bandwidth 경쟁이 생길 수 있다**는 뜻이다.

> memory만 나누면 compute는 공유되는가?

대체로 맞다. compute 실행 도메인은 하나로 남고, 메모리 locality만 나뉘는 구조로 이해하면 된다.

> 둘 다 나누면 MIG처럼 되는가?

목적은 비슷해지지만 완전히 같지는 않다. AMD는 `CPX + NPS4` 같은 모드 조합으로 하드웨어 토폴로지를 바꾸는 방식이고, NVIDIA MIG는 명시적인 GPU instance profile을 만드는 방식이다.

---

## 7. Kubernetes/OpenShift 관점

AMD GPU Operator의 Device Config Manager(DCM)는 partition profile을 Kubernetes 리소스로 관리한다.  
예를 들어 `CPX + NPS4` 프로파일을 정의하고, 노드의 GPU에 해당 partition mode를 적용하는 식이다.

개념 흐름:

```text
AMD GPU Operator 설치
→ DCM profile 정의
→ computePartition / memoryPartition 지정
→ 노드 GPU partition mode 변경
→ device plugin이 partitioned GPU 리소스 노출
→ Pod가 해당 GPU 리소스 요청
```

중요한 운영 포인트:

- partition mode 변경은 실행 중인 GPU 워크로드에 영향을 준다.
- memory partition 변경은 드라이버 재시작이나 워크로드 중단이 필요할 수 있다.
- 따라서 운영 중 즉흥 변경보다는 노드 단위 maintenance 작업으로 다루는 것이 안전하다.

---

## 8. 소비자 Radeon으로 검증 가능한 것과 불가능한 것

RX 9060 XT, RX 7900 XTX 같은 소비자 Radeon으로도 ROCm 기본 추론은 테스트할 수 있다.

가능한 테스트:

- ROCm 설치와 GPU 인식
- PyTorch/HIP 기본 동작
- llama.cpp ROCm 추론
- vLLM ROCm 경로 확인
- 컨테이너의 `/dev/kfd`, `/dev/dri` 마운트
- Kubernetes에서 AMD GPU 리소스 노출과 Pod 스케줄링

하지만 아래는 소비자 Radeon으로 제대로 검증하기 어렵다.

- MI300X급 HBM 메모리 동작
- Instinct RAS/ECC/telemetry
- xGMI/Infinity Fabric 기반 다중 GPU 통신
- AMD Instinct partitioning
- 대규모 RCCL multi-GPU 스케일링
- 서버급 GPU 운영 프로파일

따라서 소비자 Radeon은 **ROCm 경로 입문/연동 테스트용**으로는 좋지만, **서버급 AMD GPU 기능 검증용**으로는 부족하다.

---

## 9. 실무 판단 기준

추론 워크로드 기준으로는 아래처럼 구분하면 된다.

| 목적 | 적합한 테스트 |
|---|---|
| AMD ROCm이 어떻게 설치되고 동작하는지 학습 | 소비자 Radeon으로 가능 |
| vLLM/llama.cpp가 AMD에서 어디까지 도는지 확인 | 소비자 Radeon으로 가능 |
| RHOAI나 Kubernetes에서 AMD GPU 스케줄링 흐름 확인 | 소비자 Radeon으로 일부 가능 |
| MI300X partitioning 운영 검증 | Instinct 필요 |
| HBM 대용량 모델/성능 검증 | Instinct 필요 |
| 고객사 서버급 AMD GPU 아키텍처 검증 | Instinct 기반 환경 필요 |

핵심 결론:

> AMD partitioning은 MPS처럼 단순 공유가 아니라 MIG와 비슷한 문제 영역의 하드웨어/토폴로지 분할이다.  
> 다만 NVIDIA MIG처럼 정해진 GPU 인스턴스를 만드는 방식이 아니라, AMD Instinct의 compute partition과 memory partition 모드를 조합하는 방식이다.

---

## 10. 참고 자료

- AMD Instinct MI300X GPU Partitioning Overview: <https://instinct.docs.amd.com/projects/amdgpu-docs/en/latest/gpu-partitioning/mi300x/overview.html>
- AMD GPU Operator DCM partition profiles: <https://instinct.docs.amd.com/projects/gpu-operator/en/main/dcm/applying-partition-profiles.html>
- AMD SMI GPU partitioning: <https://rocm.docs.amd.com/projects/amdsmi/en/develop/conceptual/partition.html>
- ROCm blog - MI300 compute and memory partition modes: <https://rocm.blogs.amd.com/software-tools-optimization/compute-memory-modes/README.html>
