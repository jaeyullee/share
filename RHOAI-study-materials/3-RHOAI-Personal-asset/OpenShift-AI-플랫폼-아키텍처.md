# OpenShift AI 플랫폼 아키텍처

> OCP 엔지니어 관점 공부자료 | 예상 읽기 시간: 10분

> **이 문서는 KServe 배포모드·KPA/KEDA 오토스케일링·ModelCar 빌드 심화 레이어다.** RHOAI 전반·MLOps 라이프사이클·GPU 통신 등 종합은 SSOT [[rhoai-mlops-knowledge]], 입문·용어는 [[RHOAI-기초-용어정리]] 참조.

---

## 1. RHOAI가 뭔가요? (30초 요약)

OpenShift AI(RHOAI)는 OCP 위에 올라가는 **AI 운영 레이어**다. 쉽게 말하면, OCP가 컨테이너 운영체제라면 RHOAI는 그 위에서 돌아가는 "AI 전용 앱스토어 + 운영 콘솔"이다.

데이터 과학자는 Jupyter 노트북에서 모델을 만들고, 엔지니어는 KServe로 그 모델을 서비스로 배포한다. 둘 다 같은 OCP 클러스터 위에서 돌아간다.

**업스트림 관계**(ODH → RHODS → RHOAI 계보)와 "조립품으로서의 RHOAI" 설계 철학은 [[rhoai-mlops-knowledge]] §1 참조.

---

## 2. 핵심 컴포넌트 한눈에 보기

| 컴포넌트 | 역할 | OCP 비유 |
|----------|------|----------|
| **워크벤치** | 데이터 과학자 개발 환경 (Jupyter) | `oc exec`로 들어가는 개발용 Pod |
| **클러스터 스토리지** | 워크벤치 데이터 영속 저장 | PVC (Persistent Volume Claim) |
| **데이터 연결** | S3 버킷 연결 설정 | ConfigMap + Secret 조합 |
| **데이터 과학 파이프라인** | ML 워크플로 자동화 | Tekton Pipeline (Elyra UI로 생성) |
| **모델 서빙** | 학습된 모델을 API로 노출 | Deployment + Service + Route |
| **모델 모니터링** | 서빙 중인 모델 성능 추적 | Prometheus + Grafana |

### 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────┐
│                  OpenShift AI 대시보드               │
├──────────────┬──────────────┬───────────────────────┤
│   워크벤치   │  파이프라인  │      모델 서빙         │
│  (Jupyter)   │   (Elyra)    │     (KServe)           │
├──────────────┴──────────────┴───────────────────────┤
│              OpenShift (Kubernetes)                  │
│  Pod / PVC / Service / Route / Operator              │
└─────────────────────────────────────────────────────┘
```

---

## 3. KServe: 모델 서빙의 핵심

KServe는 Kubernetes 위에서 ML 모델을 서비스로 배포하는 프레임워크다. RHOAI에서 모델 서빙을 담당하는 핵심 엔진이다.

### 두 가지 배포 모드

```
KServe 배포 모드
├── Serverless (대시보드: "고급")
│   ├── Knative 기반
│   ├── scale-to-zero 지원 (요청 없으면 Pod 0개)
│   └── 동시 요청 수 기반 자동확장
└── RawDeployment (대시보드: "표준")
    ├── 일반 Kubernetes Deployment
    ├── CPU/메모리 기반 HPA
    └── 향후 KEDA 연동 예정
```

**언제 뭘 쓰나?**

| 상황 | 추천 모드 |
|------|-----------|
| 개발/테스트 환경, 비용 절감 우선 | Serverless (scale-to-zero) |
| 프로덕션, 즉시 응답 필요 | RawDeployment |
| LLM 고급 오토스케일링 | Serverless + KEDA (향후) |

### KServe 설치 의존성

KServe를 쓰려면 아래 오퍼레이터가 먼저 설치되어야 한다. OCP 엔지니어 입장에서 "사전 조건 체크리스트"다.

```
필수 오퍼레이터
├── Red Hat OpenShift Serverless (Knative)
├── Red Hat OpenShift Service Mesh (Istio)
└── Open Data Hub (ODH)

설치 순서
1. OperatorHub에서 위 3개 설치
2. DataScienceClusterInitialization(DSCI) 생성 → Istio 제어 플레인 구성
3. DataScienceCluster(DSC) 생성 → Knative Serving 배포
4. DSC에서 kserve.managementState: Managed 설정
```

---

## 4. 자동확장 (Autoscaling) 심화

### 4-1. Knative KPA (기본)

Knative는 **동시 요청 수(concurrency)**를 기준으로 Pod를 늘리고 줄인다.

```
요청 0개 → Pod 0개 (scale-to-zero)
요청 급증 → Pod 자동 추가
요청 감소 → Pod 자동 제거
```

**핵심 설정값:**

```yaml
annotations:
  autoscaling.knative.dev/target: "2"          # Pod당 목표 동시 요청 수
  autoscaling.knative.dev/scale-down-delay: "10m"  # 축소 전 대기 시간
  autoscaling.knative.dev/scale-to-zero-pod-retention-period: "1m"  # 0개 전환 전 유지
```

**주의:** LLM은 요청 1건이 수십 초 걸릴 수 있다. 기본 target 100은 너무 높다. 실제 테스트로 적정값을 찾아야 한다.

### 4-2. KEDA (고급, 추론 특화)

KPA의 한계: 무거운 요청과 가벼운 요청을 구분 못 한다. 입력 토큰 3000개짜리 요청과 10개짜리 요청이 동시성 카운트에서 똑같이 1로 잡힌다.

KEDA는 **실제 추론 지표**를 보고 확장한다.

```
vLLM 메트릭 → Prometheus → KEDA ScaledObject → HPA → Pod 수 조정
```

**핵심 메트릭:**

| 메트릭 | 의미 | 임계값 예시 |
|--------|------|-------------|
| `vllm:num_requests_waiting` | 대기 중인 요청 수 | 5개 초과 시 확장 |
| `vllm:gpu_cache_usage_perc` | GPU KV Cache 사용률 | 80% 초과 시 확장 |
| `vllm:time_per_output_token_seconds` | 토큰당 생성 시간 (ITL) | SLO 기준 설정 |

**성능 비교 결과 (이질적 워크로드 기준):**

| 방식 | ITL | 성공률 | GPU 활용 |
|------|-----|--------|----------|
| KPA (target=100) | ~87ms | 낮음 | 낮음 |
| KPA (target=10) | ~80ms | 중간 | 중간 |
| KEDA | ~70ms | 86.9% | 최고 |

결론: 이질적 워크로드(실제 운영 환경)에서는 KEDA가 명확히 우세하다.

### 4-3. KEDA 구성 핵심 절차

```
1. InferenceService에 Prometheus scrape annotation 추가
2. OpenShift user-defined project monitoring 활성화
3. KEDA용 ServiceAccount + RBAC 설정
4. cluster-monitoring-view 권한 부여
5. Prometheus 접근용 Secret + TriggerAuthentication 생성
6. ScaledObject 생성 (대상 Deployment, min/max replica, 트리거 조건)
```

---

## 5. ModelCar: 모델을 컨테이너로 패키징

### 기존 방식 vs ModelCar

```
기존 방식:
모델 파일 → S3 버킷 업로드 → KServe가 S3에서 다운로드 → 서빙

ModelCar 방식:
모델 파일 → OCI 이미지 빌드 → 컨테이너 레지스트리 푸시 → KServe가 이미지 pull → 서빙
```

### 빌드 방법 (2단계 빌드)

```dockerfile
# 1단계: 모델 다운로드
FROM python:3.11 AS builder
RUN pip install huggingface-hub
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('ibm-granite/granite-3.1-2b-instruct', local_dir='/models')"

# 2단계: 경량 런타임 이미지
FROM registry.access.redhat.com/ubi9/ubi-micro
COPY --from=builder /models /models
```

**핵심 규칙:** 모델 파일은 반드시 `/models` 경로에 있어야 한다.

### 장단점

| 장점 | 단점 |
|------|------|
| S3 버킷 관리 불필요 | 이미지 크기 = 모델 크기 |
| 컨테이너 레지스트리 기반 표준화 | 대형 LLM은 이미지 관리 어려움 |
| 노드 캐시 후 재기동 빠름 | 첫 배포 시 KNative timeout 주의 |
| 환경 간 이동성 향상 | 초대형 이미지가 노드 캐시 압박 |

**이미지 크기 참고:**
- Granite 2B: ~5GB
- Granite 8B: ~15GB
- Llama 3.1 405B: ~900GB (사실상 ModelCar 부적합)

---

## 6. 워크벤치 확장: RStudio + Snorkel

RHOAI 워크벤치는 Jupyter만 지원하는 게 아니다. 커스텀 이미지를 빌드해서 등록하면 다른 IDE도 쓸 수 있다.

### RStudio Server 통합

```
1. BuildConfig로 RStudio Server 이미지 빌드 (~7분, CUDA 버전은 ~25분)
2. ImageStream에 라벨 추가:
   oc label imagestream rstudio-server-rhel9 opendatahub.io/notebook-image=true
3. RHOAI 대시보드에서 워크벤치 생성 시 RStudio 선택 가능
```

R 언어 기반 데이터 분석이 필요한 팀에 유용하다.

### Snorkel (약한 지도학습)

수작업 라벨링 없이 **라벨링 함수**로 학습 데이터를 자동 생성하는 라이브러리다. RHOAI PyTorch 워크벤치에서 `snorkel-tutorials` 저장소를 클론해 바로 실습할 수 있다.

---

## 7. 핵심 정리

```
RHOAI = OCP 위의 AI 운영 레이어
  ├── 워크벤치 (Jupyter/RStudio) → 모델 개발
  ├── 파이프라인 (Elyra/Tekton) → 워크플로 자동화
  ├── KServe → 모델 서빙 (Serverless / RawDeployment)
  │     ├── Knative KPA → 동시성 기반 오토스케일링
  │     └── KEDA → 추론 메트릭 기반 오토스케일링 (권장)
  ├── ModelCar → OCI 이미지 기반 모델 패키징
  └── 모델 모니터링 → Prometheus + 대시보드
```

**OCP 엔지니어가 기억할 것:**
- KServe 설치 전 Serverless + Service Mesh 오퍼레이터 먼저
- LLM 오토스케일링은 KEDA + Prometheus 메트릭 조합이 정답
- ModelCar는 S3 대신 컨테이너 레지스트리로 모델 배포
- scale-to-zero는 비용 절감에 좋지만 콜드 스타트 지연 감수해야 함

---

*참고 소스: 98-Wiki-Raws/0409-ai-study/platform 카테고리 PDF 16종*
