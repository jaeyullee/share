---
title: LLM 벤치마킹 & GuideLLM 실전 가이드
date: 2026-04-10
tags: [ai, study, evaluation, guidellm, benchmarking, vllm, openshift-ai]
---

# LLM 벤치마킹 & GuideLLM 실전 가이드

> OCP 엔지니어 관점 | 10분 분량

---

## 왜 LLM 벤치마킹이 필요한가

LLM을 OpenShift에 배포하기 전에 반드시 답해야 할 질문들이 있다.

- 이 모델이 우리 트래픽을 감당할 수 있나?
- GPU 몇 장이 필요한가?
- 응답 속도가 사용자 경험 기준을 충족하나?
- 양자화 모델로 바꾸면 성능이 얼마나 떨어지나?

전통적인 부하 테스트 도구(JMeter, k6)는 LLM에 맞지 않는다. LLM은 요청 처리 시간이 수초~수분이고, 스트리밍 응답이며, 고가 GPU에 의존한다. **GuideLLM**은 이 문제를 위해 만들어진 도구다.

---

## GuideLLM 핵심 지표

비유하자면, LLM 서비스는 **음식 배달 앱**이다.

| 지표 | 배달 비유 | 의미 |
|------|-----------|------|
| **TTFT** (Time to First Token) | 주문 접수 확인 시간 | 첫 응답까지 걸리는 시간 |
| **ITL** (Inter-Token Latency) | 음식 조리 속도 | 토큰 간 생성 간격 |
| **E2E Latency** | 문 앞 도착까지 총 시간 | 전체 요청 완료 시간 |
| **RPS** (Requests Per Second) | 동시 주문 처리 수 | 초당 처리 요청 수 |
| **Throughput** | 시간당 배달 건수 | 초당 출력 토큰 수 |

**대화형 서비스에서 TTFT가 가장 중요하다.** 사용자는 첫 글자가 나오기까지 기다리는 시간을 가장 길게 느낀다.

---

## GuideLLM 실행 방법

### 기본 벤치마킹

```bash
guidellm benchmark \
  --target http://vllm-service.namespace.svc.cluster.local:8000 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --data "prompt_tokens=512,output_tokens=256" \
  --rate-type concurrent \
  --rate 1,2,4,8 \
  --max-seconds 300 \
  --output-dir /results \
  --outputs json,html
```

### 주요 옵션

| 옵션 | 설명 |
|------|------|
| `--target` | 추론 서버 엔드포인트 |
| `--rate-type concurrent` | 고정 동시성 부하 |
| `--rate 1,2,4` | 동시 요청 수 (여러 값 지정 가능) |
| `--max-seconds 300` | 각 테스트 최대 5분 |
| `--data` | 합성 워크로드 정의 |

### 왜 내부 서비스 DNS를 써야 하나

```
# 잘못된 방법 (외부 Route 사용)
--target https://vllm-route.apps.cluster.example.com

# 올바른 방법 (내부 ClusterIP 사용)
--target http://vllm-service.namespace.svc.cluster.local:8000
```

외부 Route를 통하면 Ingress 지연, TLS 오버헤드, 네트워크 홉이 섞인다. 실제 추론 엔진 성능만 측정하려면 내부 서비스를 직접 사용해야 한다.

---

## OpenShift에서 GuideLLM 실행 (Job 방식)

GuideLLM은 클러스터 내부에서 Job으로 실행한다.

```yaml
# 필요한 리소스
- PVC: 모델 가중치 (/mnt/models)
- PVC: 토크나이저 (/mnt/tokenizer)
- PVC: 결과 저장 (/results)
- Job: GuideLLM 실행
- Service: vLLM 내부 노출 (ClusterIP)
```

결과 수집:
```bash
# helper pod로 결과 복사
oc cp helper-pod:/results ./local-results

# JSON 결과 재표시
guidellm benchmark from-file ./local-results/benchmark.json
```

---

## 에어갭 환경 벤치마킹

인터넷이 차단된 환경에서도 벤치마킹이 가능하다.

### 준비 단계

```bash
# 1. 연결된 환경에서 이미지 미러링
oc-mirror --config mirror-config.yaml file://mirror-output

# 2. 내부 레지스트리에 업로드
oc-mirror --from file://mirror-output docker://internal-registry.example.com

# 3. ICSP 적용 (외부 요청을 내부 미러로 리디렉션)
oc apply -f imagecontentsourcepolicy.yaml
```

GuideLLM은 자체 텍스트 코퍼스를 포함하므로 **외부 데이터셋 없이 오프라인 실행**이 가능하다.

---

## 과포화 문제: 벤치마킹 비용의 함정

### 과포화란?

서버가 유입 요청을 감당하지 못해 대기열이 쌓이는 상태다. 이 상태에서 측정한 지표는 왜곡돼 무의미하다.

```
정상 상태: 요청 → 즉시 처리 → 응답
과포화 상태: 요청 → 대기열 누적 → 처리 지연 → 왜곡된 지표
```

### 실제 규모

Red Hat/Jounce 팀의 경험:
- 잠재 조합: **7,488개** (모델 × GPU 종류 × GPU 수 × 부하 × 프롬프트 유형)
- 실제 실행: **4,506개**
- 과포화로 무효화: **절반 이상**
- 낭비된 GPU 시간: **약 50%**

### 해결 방향: OSD (Over-Saturation Detection)

과포화를 조기에 감지해 테스트를 자동 중단한다. 고정 임계값으로는 안 되고, TTFT·ITL 같은 LLM 전용 지표를 활용한 데이터 기반 접근이 필요하다.

---

## 용량 계획에 활용하기

벤치마킹 결과로 필요한 서버 수를 역산할 수 있다.

```
측정 결과: 단일 서버에서 10.69 RPS로 99% SLO 충족
목표 트래픽: 1,000 RPS

필요 서버 수 = 1,000 / 10.69 ≈ 94대
```

이 계산이 가능하려면 **스윕(sweep) 모드**로 다양한 부하 수준을 측정해야 한다.

---

## OCP 엔지니어가 기억할 것

1. **배포 전 반드시 GuideLLM으로 검증**. 실제 트래픽 패턴을 시뮬레이션해야 의미 있는 결과가 나온다.
2. **내부 ClusterIP 서비스로 벤치마킹**. 외부 Route는 네트워크 지연이 섞인다.
3. **TTFT가 대화형 서비스의 핵심 지표**. 사용자 경험과 가장 직결된다.
4. **에어갭 환경도 oc-mirror + ICSP로 해결**. GuideLLM은 오프라인 실행이 가능하다.
5. **과포화 상태의 지표는 버려야 한다**. 의미 없는 데이터로 용량 계획을 세우면 안 된다.
