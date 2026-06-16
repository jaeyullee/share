# RHOAI / MLOps / k8s AI 인프라 학습 정리

> Red Hat OpenShift AI(RHOAI)를 중심으로 한 MLOps · 쿠버네티스 기반 ML/AI 인프라 지식 정리.
> 딜리버리 관점에서 "조립품으로서의 RHOAI"와 각 구성요소의 업스트림 동작을 이해하는 데 초점.

> **폴더 3 RHOAI 노트 계층** (이 문서가 종합 SSOT): 입문·용어·GPS 로드맵은 [[01-RHOAI-기초-용어정리]], KServe 배포모드·KPA/KEDA 오토스케일링·ModelCar 빌드 심화는 [[02-OpenShift-AI-플랫폼-아키텍처]]. 개념 중복 시 본 문서를 단일 출처로 둔다.

---

## 1. RHOAI 개요와 포지셔닝

### 1.1 정의
- RHOAI는 단일 소프트웨어가 아니라 **OpenShift(쿠버네티스) 위에서 동작하는 통합 AI/ML 플랫폼**이다.
- 본질은 **오픈소스 조립품(curation)**: KFP·KServe·Tekton·Argo CD·Feast·Ray·llm-d·vLLM 등 다수의 독립 오픈소스를 오퍼레이터로 묶은 것.
- 업스트림 커뮤니티 프로젝트는 **Open Data Hub(ODH)**이며, RHOAI는 그 상용·지원 배포판(OpenShift가 쿠버네티스에 대해 갖는 관계와 동일).
- 제품명 변천: **OpenShift Data Science → OpenShift AI**. "Data Science"에서 "AI"로 바뀐 것은 스코프가 MLOps 중심에서 LLM/GenAI까지 포괄하는 방향으로 확장됐음을 의미.

### 1.2 정확한 범주
- "MLOps 도구"는 절반의 정의. 더 정확히는 **"OpenShift 위의 통합 AI 플랫폼"**.
- 세 기둥:
  1. **MLOps 라이프사이클** (실험 → 파이프라인 → 서빙 → 모니터링) — 가장 성숙한 핵심
  2. **LLM/GenAI 서빙·구축** (MaaS · llm-d · vLLM · Llama Stack · RAG) — 급성장 영역
  3. **분산 컴퓨팅·GPU 기반** (Ray · Kubeflow Trainer · Kueue) — 위 둘을 떠받치는 토대

### 1.3 설계 철학 (생태계 진화 관점)
- **플랫폼 = 모놀리스가 아니라 best-of-breed 조립품.** 과거 Kubeflow 모놀리스가 KServe·Model Registry·Pipelines 등으로 언번들링됨.
- **Operator/CRD가 통합 레이어.** ML 라이프사이클의 각 단계가 선언적 k8s 오브젝트(CR)가 되며, 그 결과 GitOps가 가능해짐.
- **ML = 1급 쿠버네티스 워크로드.** DevOps의 원칙(선언적·GitOps·공급망 보안)을 ML에 그대로 적용.
- **데이터·모델 차원의 추가.** MLOps = DevOps + 데이터 버저닝(DVC·Feast) + 모델 관리(Registry·모델 스캔).
- **공급망 보안의 ML 확장.** SBOM(Syft)·서명(Sigstore/cosign)·취약점 스캔(StackRox/ACS)·모델 스캔(modelscan)이 모델 아티팩트까지 적용됨.

---

## 2. MLOps 라이프사이클

### 2.1 inner loop → outer loop
- **inner loop**: 사람이 노트북에서 대화형으로 실험하는 단계(수동).
- **outer loop**: 데이터 버전·git 변경·메트릭 알림 등 트리거에 의해 학습·배포가 자동 실행되는 단계.
- 핵심 전환: 검증된 실험을 재현 가능·자동화된 파이프라인으로 "굳히는" 것.

### 2.2 전형적 흐름
```
실험(워크벤치/노트북)
  → 파이프라인화(Elyra/KFP)
  → MLOps 자동화(Tekton + Argo CD)
  → 서빙(KServe)
  → 모니터링(TrustyAI + Prometheus/Grafana)
  → 데이터/피처(DVC / Feast)
  → [+ LLM 축: MaaS / llm-d / Llama Stack]
```

### 2.3 재학습 트리거 3종
| 트리거 | 소스 | 의미 |
|---|---|---|
| 코드 변경 | 소스 레포 push | 모델 만드는 방법이 바뀜 |
| 데이터 변경 | DVC 데이터 버전 | 새 데이터 도착 |
| 모델 이상 | 모니터링 알림(드리프트) | 성능 저하 → 재학습 |

---

## 3. 실험·작성 환경: 워크벤치 / 노트북 / Elyra / KFP

### 3.1 워크벤치 (Workbench)
- 노트북 앱이 아니라 **하나의 쿠버네티스 커스텀 리소스(CR)**.
- 클릭하면 미리 빌드된 이미지 + GPU/CPU 할당 + PVC + S3(MinIO) 커넥션 + Model Registry 연결이 붙은 Pod가 기동.
- 역할: **코드 작성 + 대화형 실행 + 파이프라인 트리거하는 개발 IDE 파드**.
- 주의: 워크벤치는 "ML이 도는 환경"이 아니다. 대화형 노트북 셀 실행만 워크벤치 파드 안에서 돌고, **파이프라인 실행은 별도 파드**(클러스터)에서 돈다. 그래서 워크벤치를 꺼도 파이프라인 run은 계속됨.
- 이미지 예: Jupyter(Standard Data Science), code-server.

### 3.2 노트북
- ML 로직을 담은 Python 코드(대화형). 셀 단위 실험.

### 3.3 Elyra
- Jupyter 워크벤치 안에 들어있는 **JupyterLab 확장(비주얼 파이프라인 에디터)**.
- 드래그앤드롭 캔버스에서 **노트북(.ipynb)을 그대로** 스텝으로 연결 → 파이프라인화. 코드 수정 불필요.
- 단위 = 노트북 통째. 빠른 프로토타이핑용 저코드 방식.
- 결과물은 **같은 DSP/KFP 백엔드**로 제출됨(KFP run과 동일한 화면에 표시).

### 3.4 KFP (Kubeflow Pipelines)
- 코드 기반 파이프라인 작성 방식 + 백엔드 서버.
- 단위 = **함수(component)**. 노트북 로직을 `@dsl.component` 함수로 리팩터링해 DAG로 엮음.
- production급 기능: 버전 관리, 메타데이터·계보 추적, 캐싱, 재시도, 파라미터화, 실험(run) 비교.

#### KFP 구성 3종
| 구성 | 역할 | 위치 |
|---|---|---|
| (a) SDK | Python 작성 + IR 컴파일 | 클라이언트(워크벤치) |
| (b) 서버/API + 메타데이터 | run/pipeline/experiment 저장 | 네임스페이스 내 파드 |
| (c) 실행 엔진 | DAG를 파드로 실행 | Argo Workflows |

#### KFP 코드 예시 (구조)
```python
@dsl.pipeline(name='kfp-training-pipeline')
def training_pipeline(hyperparameters: dict, model_name: str, version: str):
    fetch_task      = fetch_data()
    validation_task = validate_data(dataset=fetch_task.outputs["dataset"])
    preprocess_task = preprocess_data(in_data=fetch_task.outputs["dataset"])
    preprocess_task.after(validation_task)
    training_task   = train_model(train_data=preprocess_task.outputs["train_data"],
                                  hyperparameters=hyperparameters)
    convert_task    = convert_keras_to_onnx(keras_model=training_task.outputs["trained_model"])
    eval_task       = evaluate_keras_model_performance(model=training_task.outputs["trained_model"])
    register_task   = push_to_model_registry(model=convert_task.outputs["onnx_model"],
                                             metrics=eval_task.outputs["metrics"])
```
- 스텝 간에는 파일이 아니라 **타입 있는 아티팩트**(`Dataset`, `Model`, `Metrics`)가 흐르며 계보가 추적됨.
- 로직(알맹이)은 노트북에서 복사 재사용하되, **함수 시그니처·아티팩트 입출력·DAG는 새로 작성**. 실행 시 component 코드(혹은 import한 .py)가 모두 컨테이너 이미지에 포함돼야 함.

### 3.5 진행 단계 = 관계
```
노트북(수동) → Elyra(노트북 통째 연결, 저코드) → KFP(함수로 재작성, production급)
```
워크벤치는 이 세 단계가 모두 일어나는 공통 작업실.

---

## 4. KFP 실행 메커니즘 & DAG

### 4.1 작성 → 파드 실행 경로
```
KFP SDK(Python)
  → compile → IR YAML (각 component = 컨테이너 스펙)
  → submit → DSP/KFP API 서버 (ds-pipeline-dspa.<ns>.svc:8443)
  → 변환 → Argo Workflows Workflow CR
  → 실행 → component마다 파드 1개씩 OCP에 스케줄
  → 대시보드 Pipelines > Runs 에 DAG·아티팩트·메트릭 표시
```
- 파드 간 메모리 공유 불가 → 아티팩트는 **S3/MinIO(또는 PVC)** 경유로 전달.

### 4.2 Argo Workflows (KFP 백엔드)
- 쿠버네티스 네이티브 **범용 워크플로 엔진**. `Workflow` CR의 DAG를 보고 스텝마다 파드 실행.
- 그 자체는 ML을 모름. KFP가 그 위에 ML 의미(아티팩트·실험·캐싱·SDK)를 입힘.
- **주의**: Argo Workflows ≠ Argo CD. 전자는 DAG 실행 엔진, 후자는 GitOps 배포 컨트롤러(둘 다 CNCF Argo 프로젝트지만 별개).
- RHOAI 내장 Argo Workflows는 KFP 내부 부품으로만 깔리며, 사용자가 직접 `Workflow` CR로 쓰는 것은 비지원.

### 4.3 DSP 백엔드 버전 변천 (생태계 진화)
- **DSP 1.x**: KFP v1을 `kfp-tekton`으로 컴파일 → **Tekton을 실행 엔진**으로 사용(Red Hat 고유 구현).
- **DSP 2.x** (OpenShift AI 2.9+): kfp-tekton 폐기 → **Argo Workflows를 실행 엔진**으로 채택 → 업스트림 Kubeflow Pipelines와 정렬.
- 함의: 과거엔 KFP의 실행 엔진이 Tekton이었기에 KFP·Tekton 관계가 혼동되기 쉬움. 현재는 분리됨.

### 4.4 DAG (Directed Acyclic Graph)
- **방향성 비순환 그래프**. 작업(노드)과 의존관계(엣지)로 구성.
- Directed: "A 다음 B" 방향이 있음. Acyclic: 되돌아오는 순환 금지(→ 종료 보장). Graph: 노드+엣지.
- 갈라짐(병렬)·합쳐짐(동기화)을 표현. 엔진은 의존성 없는 노드부터 띄우고 선행이 끝나면 다음을 띄움.
- KFP/Elyra/Tekton/Argo Workflows 모두 DAG 기반.

---

## 5. CI/CD & GitOps: Tekton / Argo CD

### 5.1 세 도구의 역할 (계층적)
| 도구 | 역할 | 페르소나 언어 |
|---|---|---|
| **KFP** | ML 작업 실행 엔진(훈련 DAG) | 데이터셋·모델·하이퍼파라미터·메트릭 |
| **Tekton (OpenShift Pipelines)** | 이벤트 반응 + 전체 CD 절차 오케스트레이션 | workspace·git clone·이미지 빌드·트리거 |
| **Argo CD (OpenShift GitOps)** | git ↔ 클러스터 상태 reconcile(선언적 배포) | "git이 이러니 클러스터를 맞춰라" |
- 동료(peer)가 아니라 **계층 관계**: Tekton이 KFP를 호출하고, Argo CD는 모델·도구·파이프라인까지 전부 배포.

### 5.2 전체 트리거 체인
```
소스 레포 push
  → webhook → Tekton EventListener → PipelineRun 시작
  → (2번째 스텝) KFP 훈련 파이프라인 트리거 → 모델 생성·S3 저장·Registry 등록
  → test 환경 YAML 갱신 후 git commit (test는 자동)
  → prod 환경용 변경은 PR 생성(승인 게이트)
  → 사람이 PR 머지 → Argo CD가 prod에 KServe 배포
  → post-deployment(Tekton) 파이프라인 → Model Registry 메타데이터를 prod 반영으로 갱신
```

### 5.3 Tekton Triggers 구성요소
- **EventListener**: webhook HTTP 요청을 받는 수신 엔드포인트.
- **TriggerBinding**: 요청에서 값(커밋ID·레포명 등) 추출.
- **TriggerTemplate**: 그 값으로 생성할 PipelineRun 정의.

### 5.4 Webhook
- 이벤트(push·머지) 발생 시 정해진 URL로 HTTP POST를 보내는 푸시형 알림(폴링의 반대).
- KFP는 자체적으로 webhook 수신 기능이 없음 → Tekton EventListener가 받아 KFP API 호출로 변환.

### 5.5 KFP 트리거 방식
- KFP가 스스로 할 수 있는 트리거: **API 호출**(`create_run`), **Recurring Run(스케줄/cron)**.
- KFP가 못 하는 것: git webhook 같은 외부 이벤트 수신·해석. → Tekton/Argo Events/CI 도구가 앞단에서 처리.
- KFP API는 **정해진 REST/gRPC 계약(엔드포인트·인증 토큰·본문)**에 맞는 호출만 수신. webhook raw 페이로드는 형식이 달라 번역 필요.

### 5.6 환경 구분: 브랜치 vs 디렉터리/overlay
- GitOps 주류 권장: **환경은 브랜치가 아니라 디렉터리(overlay/폴더)로 구분.**
- 브랜치 단위 환경 구분은 drift·머지 충돌 등으로 흔히 안티패턴으로 평가됨.
- 도구: Kustomize(base+overlay) 또는 Helm(chart+values). 둘 다 "base 템플릿 + 환경별 차이 패치" 구조.

#### 예시 구조 (Helm + ApplicationSet)
```
gitops 레포 (브랜치 main 하나)
├── appset-test.yaml        ← test용 ApplicationSet
├── appset-prod.yaml        ← prod용 ApplicationSet
└── model-deployments/
    ├── test/<app>/config.yaml   ← test 환경 값(version 등)
    └── prod/<app>/config.yaml   ← prod 환경 값
별도 Helm 차트 레포
└── charts/.../              ← InferenceService 등 템플릿(base)
```
- 환경 구분 = 디렉터리(test/ vs prod/), 환경 차이 = Helm chart + config.yaml(values), Argo CD ApplicationSet이 폴더별로 차트 렌더링.
- 승격(promotion) = prod 폴더 `config.yaml`의 version을 바꾸는 PR.

### 5.7 PR(Pull Request)/MR의 본질
- PR/MR은 솔루션 명칭 차이(GitHub=PR, GitLab=MR, Gitea 등). 본질은 "브랜치 X의 변경을 브랜치 Y에 합치자는 제안".
- **상위 브랜치 머지 전용이 아니다.** GitOps 승격에선 "config 한 줄 바꾼 짧은 브랜치 → main" 형태로 쓰임. 즉 환경≠브랜치지만 PR은 여전히 브랜치→브랜치.
- 역할: 보호된(protected) 브랜치를 안전하게 바꾸는 **승인·감사·게이트** 장치. (자동 검증 연결, 감사 추적, 롤백 용이)
- 패턴: test는 PR 없이 자동 반영, prod만 protected main + PR 승인. 실운영에선 prod 정의를 별도 레포로 분리 권장.

---

## 6. 모델 관리 & 서빙

### 6.1 세 개념 구분 (축이 다름)
| 개념 | 정의 | 비유 |
|---|---|---|
| **S3/MinIO** | 모델 파일(ONNX 등)이 실제 저장되는 곳 | 창고 |
| **Model Registry** | 모델 버전·메타데이터·계보·배포상태를 가리키는 카탈로그(포인터) | 장부/색인 |
| **Model Catalog** | 배포 가능한(큐레이션된) 모델을 발견·선택하는 진열장 | 진열대 |
| **OCI ModelCar** | 모델 파일을 OCI 이미지로 포장하는 배포 운반 방식 | 포장·운송 |
- Registry는 저장소가 아니라 메타데이터 인덱스. 지워도 S3의 모델은 남음.

### 6.2 모델 서빙: S3 직접 vs OCI(ModelCar)
| | S3에서 직접 | 모델카(OCI) |
|---|---|---|
| 모델 위치 | S3/MinIO 객체 | 컨테이너 이미지 레이어 |
| 배포 시 | KServe가 런타임에 다운로드 | 이미지를 사이드카로 마운트 |
| 불변성 | 약함(같은 키 덮어쓰기 가능) | 강함(다이제스트가 바이트 고정) |
| 서명·스캔·SBOM | 적용 까다로움 | 컨테이너 공급망 도구 그대로 적용 |
| 동기 | 단순·교체 쉬움 | 재현성·공급망 거버넌스 |
- ModelCar의 핵심 가치는 "서빙 방법"이 아니라 **불변성·재현성(pinning)·공급망 적용**. 서빙 경로는 그 가치를 소비하는 출구.
- 동기는 "재기동 초기화"가 아니라 "재기동·재배포·복제 어디서든 동일 바이트 보장(고정)". 모델은 정적 파일이라 초기화할 상태가 없음.

### 6.3 2026 시점 서빙 동향
- 단일 승자는 없고 용도별로 갈림. 모멘텀은 OCI 쪽.
- **소형/전통 예측 모델**: S3/URI가 여전히 무난한 기본값(GA·안정).
- **LLM/대형 모델·공급망 거버넌스 중시**: OCI 기반이 부상(S3 다운로드가 대형 모델 콜드스타트 병목).
- 진화 경로: **S3 직접 → modelcar(사이드카+심볼릭링크 우회) → 네이티브 쿠버네티스 OCI Image Volume(`oci://`)**.
  - OCI Image Volume(KEP-4639): k8s 1.31 알파, 1.33 베타. 단 런타임 지원 격차로 기본 비활성(CRI-O 1.33부터 베타, containerd 추격 중).
- 더 큰 화두는 LLM 서빙(vLLM)과 모델의 OCI 아티팩트화(Docker Model Runner 2025.9 GA 등).

### 6.4 KServe
- 쿠버네티스 모델 서빙의 사실상 표준. InferenceService CR. Knative scale-to-zero + KEDA 이벤트 기반 오토스케일과 결합.
- 서빙 = 서비스형 워크로드(계속 대기). 다양한 ServingRuntime(예: MLServer, vLLM) 선택 가능.

---

## 7. 실험관리 & 데이터/피처

### 7.1 MLflow
- 오픈소스 ML 라이프사이클 도구. 핵심은 **실험 추적**(run별 파라미터·메트릭 기록·비교)과 자체 Model Registry.
- KFP와 다른 종목: KFP=오케스트레이션(실행), MLflow=기록·관리. 멀티스텝 DAG 오케스트레이션 엔진은 아님(Projects는 단일 실행 포장 수준).
- 보완 관계: KFP component 안에서 `mlflow.log_*`로 결과를 기록하는 식으로 함께 사용.

| 항목 | KFP(DSP) | MLflow |
|---|---|---|
| 1차 목적 | 워크플로 실행/오케스트레이션 | 실험 추적 + 모델 관리 |
| DAG 실행 | O(핵심) | X |
| 실험 비교 UI | 보조 | O(핵심) |
| 이벤트/스케줄 트리거 | O | X |
| k8s 의존성 | 강함 | 약함(어디서나) |

### 7.2 Feast (Feature Store)
- 이름: **Fea**ture **St**ore의 약자이자 영단어 feast(잔치) 중의적 작명. 발음 "피스트".
- 정의: ML 피처(모델 입력 변수)를 중앙에서 정의·저장·제공하는 피처 스토어. 현재 Linux Foundation 산하.
- 푸는 문제:
  1. **학습-서빙 불일치(training-serving skew)** 제거 — 학습·추론이 같은 피처 정의를 공유.
  2. 피처 **재사용·공유**.
- 핵심 구조: **온라인 스토어**(실시간 추론용, Redis 등 저지연) + **오프라인 스토어**(학습용, S3/Parquet 등 대량). 같은 정의에서 둘 다 제공 → skew 구조적 해결.
- **Point-in-time join**: 학습 시 "그 시점에 알 수 있던 값"만 가져와 data leakage 방지.

### 7.3 DVC
- 데이터 버저닝 도구. ETL이 데이터 버전을 git에 푸시 → 학습 자동 재실행 트리거.
- DVC(데이터 버전) ↔ Feast(피처 관리)가 MLOps "데이터 차원"의 두 기둥.

---

## 8. LLM / GenAI

### 8.1 MaaS (Models-as-a-Service)
- LLM을 중앙에서 서빙하고 여러 팀이 API로 소비하는 내부 플랫폼("사내판 OpenAI API").
- 핵심 가치는 모델이 아니라 **거버넌스**: 사용량 추적, 인증, 비용 통제, 셀프서비스, rate limit.
- 사실상 LLM(및 임베딩 등 생성형/기반 모델) 중심. 가벼운 전통 ML 모델은 일반 서빙(InferenceService)이 더 자연스러움 — MaaS의 공유·과금·게이트웨이 가치는 대형 범용 모델에서만 살아남.

### 8.2 추론 게이트웨이 (Inference Gateway)
- MaaS/llm-d 서빙 앞단의 API 게이트웨이. 인증·인가, 사용량 측정/과금, rate limit, 라우팅 처리.
- RHOAI에선 Gateway API 기반(Red Hat Connectivity Link = Kuadrant 계열)으로 구현.

### 8.3 RAG (Retrieval-Augmented Generation)
- 검색 증강 생성. LLM이 답하기 전에 외부 지식(문서·DB)에서 관련 내용을 검색해 그 근거로 답을 생성.
- 효과: 최신/사내 지식 반영, 환각(hallucination) 감소, 출처 인용.
- 흐름:
```
[준비] 문서 → 청크 분할 → 임베딩 → 벡터 DB 저장
[질의] 질문 → 임베딩 → 벡터 DB에서 유사 청크 검색 → LLM에 근거로 전달 → 답 생성
```

### 8.4 임베딩 (Embedding)
- 텍스트(이미지·음성)를 **의미 관계를 보존한 채** 연속 벡터 공간에 매핑한 것. "의미가 비슷하면 벡터도 가깝다".
- 어원: 수학의 embedding("관계 보존하며 다른 공간에 끼워넣기"). 본질은 *관계 보존*이고 벡터는 그 보존에 가장 적합한 그릇(현실에선 거의 항상 벡터지만 정의상 필수는 아님 — 쌍곡공간·분포 임베딩 등 존재).
- "벡터화"와 미묘한 차이: 벡터화=형식(숫자로 변환), 임베딩=성질(의미 구조 보존).
- RAG에서 시맨틱 검색(키워드가 달라도 의미로 검색)의 토대.
- **임베딩 모델**은 LLM과 별개의 전용·소형 모델(텍스트→벡터 출력, 생성 안 함). 벡터 DB(FAISS·Milvus·pgvector 등)와 한 세트.

### 8.5 기타 LLM 구성요소
- **llm-d**: 대형 LLM 분산 추론 k8s 프레임워크(prefill/decode 분리, KV-cache 인지 라우팅). LLMInferenceService CR.
- **vLLM**: 고성능 LLM 추론 런타임. 멀티노드 시 Ray를 분산 백엔드로 활용.
- **Llama Stack**: GenAI 앱 구축용 표준 API 계층(추론·RAG·에이전트·안전·평가). (※ Llama=모델, Llama Stack=프레임워크로 구분)
- **NeMo Guardrails**: NVIDIA의 LLM 가드레일(민감정보 탐지·콘텐츠 필터링·대화 제어).
- **MLServer (Seldon)**: 다중 프레임워크(sklearn·xgboost·MLflow 등) 모델을 표준(Open Inference/V2) 프로토콜로 서빙하는 런타임.

### 8.6 모델 종류 구분
- 전통 ML: **scikit-learn**(고전 알고리즘), **XGBoost**(그래디언트 부스팅 트리) — 정형(tabular) 데이터.
- 딥러닝/LLM: **PyTorch**(딥러닝 프레임워크)로 만든 모델, **Llama** 등.

---

## 9. 분산 컴퓨팅 & 잡 스케줄링

### 9.1 잡(Job) vs 서비스(Service)
| | 서비스형(Deployment) | 잡형(Job) |
|---|---|---|
| 수명 | 계속 대기 | 끝나면 종료 |
| ML 예 | 추론 서빙(KServe) | 학습·전처리·튜닝 |
| 자원 | 계속 점유 | 끝나면 반납(GPU 공유 가능) |
- KFP의 각 스텝, 분산 학습, 튜닝은 본질적으로 잡. 추론만 서비스.

### 9.2 Ray / KubeRay
- Ray는 학습 전용이 아니라 **범용 분산 실행 플랫폼**. 라이브러리: Ray Train(학습), Ray Tune(튜닝), Ray Data(전처리), **Ray Serve(추론)**, Ray Core.
- 역사적으론 학습·튜닝 인상이 강했으나, LLM 시대에 분산 추론(vLLM·llm-d 백엔드)으로 비중 확대 → 학습·추론 양쪽 모두 담당.
- KubeRay: Ray를 k8s에서 운영하는 오퍼레이터.

### 9.3 Kueue (잡 큐잉)
- 한정된 GPU를 여러 잡이 나눠 쓰도록 줄 세우는 쿠버네티스 네이티브 잡 큐잉 시스템.
- 동작: 파드를 바로 띄우지 않고 **자원 확보 시까지 보류(gating)** → 점유 충돌·데드락 방지(일반 k8s의 무한 Pending과 대비).
- 개념: ClusterQueue(자원 풀·할당량) / LocalQueue(팀별 큐), 우선순위·선점(preemption), 공정 공유(cohort borrowing).
- 전제: 잡이 "끝나면 GPU 반납"하기에 큐잉이 성립. 추론 서비스는 대상 아님(오토스케일로 다룸).
- 위에 얹히는 잡: PyTorchJob(Kubeflow Trainer), RayJob, KFP 스텝, 일반 k8s Job.

### 9.4 Kubeflow Trainer v2
- 분산 학습 잡(PyTorch 등)을 관리하는 차세대 Training Operator.

---

## 10. GPU 공유 & 분산 병렬화

### 10.1 GPU 나눠쓰기/묶어쓰기 스펙트럼
```
◀── 쪼개기(1 GPU를 여럿이) ──┼── 통째(1잡=1+GPU) ──┼── 묶기(여러 GPU=1작업) ──▶
   타임슬라이싱   MIG/MPS        Kueue 순번 배정       데이터/텐서/파이프라인 병렬
   (시간분할)    (공간분할)      (시간적 순번)        (NCCL·NVLink/RDMA로 묶음)
```

### 10.2 쪼개기
- **타임슬라이싱**: 한 GPU를 시간으로 번갈아 사용. 격리 없음(noisy neighbor). 가벼운 실험용.
- **MIG (Multi-Instance GPU)**: A100/H100 등에서 GPU **한 장을 하드웨어 격리 인스턴스로 분할(최대 7개)**. 전용 SM·L2·메모리 채널 → 진짜 격리.
- **MPS**: 여러 프로세스가 한 GPU 동시 공유(MIG보다 약한 격리).

### 10.3 묶어쓰기(분산 병렬화)
- **데이터 병렬**: 모델 전체 복제, 데이터를 나눠 각 GPU가 학습 후 기울기 동기화. 통신 가끔.
- **모델 병렬**(우산): 모델 자체를 쪼갬. GPU 한 장에 안 들어갈 때.
  - **텐서 병렬(intra-layer)**: 한 레이어의 행렬을 가로로 쪼개 여러 GPU가 동시 계산 후 합침. **통신 초고빈도** → 노드 내(NVLink) 적합.
  - **파이프라인 병렬(inter-layer)**: 레이어를 단계로 나눠 GPU들이 릴레이. 통신 드뭄 → 노드 간 적합. 약점: 파이프라인 버블(유휴).
- **3D 병렬**: 노드 내 텐서 병렬 + 노드 간 파이프라인 병렬 + 데이터 병렬을 토폴로지에 맞게 조합.

### 10.4 "연산을 쪼갠다"의 원리
- 신경망 레이어 = 행렬 곱 `Y = X·W`.
- 가중치 W를 열 단위로 조각내 각 GPU가 자기 조각만 계산(`X·W1`, `X·W2`…) 후 결과를 이어붙이면 안 쪼갠 결과와 동일.
- 가능한 이유: 출력의 각 열이 W의 해당 열에만 의존 → 독립 병렬 계산.
- 레이어가 이어질 때 조각난 출력을 합쳐야 함(all-gather/all-reduce) → 레이어마다 통신 발생.

---

## 11. GPU 간 통신: NVLink / RDMA / InfiniBand / CXL

### 11.1 거리(스코프)별 통신 방식
| 구간 | 방식 | CPU 우회 | 비고 |
|---|---|---|---|
| 노드 내 GPU↔GPU | **NVLink/NVSwitch** | O | NVIDIA 전용 직결, 최고속 |
| 노드 내 GPU↔GPU | **PCIe P2P (GPUDirect)** | O | NVLink 없을 때 |
| 노드 간 GPU↔GPU | **RDMA over InfiniBand/RoCE** | O | 네트워크 너머 |

### 11.2 DMA / RDMA
- **DMA**: 한 머신 안에서 장치가 CPU를 거치지 않고 메모리에 직접 접근.
- **RDMA (Remote DMA)**: 그 직접 접근을 **네트워크 너머 다른 머신의 메모리**로 확장. R=Remote.
- 한 박스 안 GPU 간 통신은 RDMA가 아니라 NVLink/PCIe P2P(로컬).

### 11.3 GPUDirect RDMA 동작 원리
- NIC가 GPU VRAM에 직접 DMA → CPU 메모리(바운스 버퍼) 우회.
- 전제:
  1. **GPU 메모리를 PCIe BAR로 노출**(NIC가 PCIe 물리주소로 접근). Large BAR / Resizable BAR로 대용량 노출.
  2. **PCIe Peer-to-Peer**: NIC↔GPU가 같은 PCIe 트리/스위치 아래 직접 통신(토폴로지·GPU-NIC affinity가 성능 좌우).
  3. **메모리 등록(registration) + pin**: 드라이버가 GPU 물리주소를 NIC 변환 테이블에 기록·고정(`nvidia-peermem` 모듈).
- 두 가지 우회: **커널 바이패스**(QP에 직접 작업) + **CPU/메모리 바이패스**(PCIe P2P).
- **NCCL**: 토폴로지를 읽어 노드 내=NVLink, 노드 간=GPUDirect RDMA를 골라 집합통신(all-reduce 등) 수행.

### 11.4 BAR(주소 윈도우)의 물리적 한계
- 32비트 BAR = 최대 4GB → 큰 VRAM 전체 노출 불가했던 시절의 병목. MMIO 주소공간도 유한.
- 해결: **64비트 BAR / Large BAR / Resizable BAR + 펌웨어 "Above 4G Decoding"**.
- 잔존 한계: MMIO 배치 충돌, IOMMU 매핑 오버헤드, PCIe 대역폭 자체. → GPUDirect RDMA를 켜려면 BIOS/펌웨어 설정 필요.

### 11.5 CXL (Compute Express Link)
- RDMA와 대비되는 별개 계층. **노드 내(scale-up)에서 CPU·GPU·메모리·장치를 캐시 일관성 있게 직접 연결**(PCIe 물리계층 위 프로토콜).
| 항목 | RDMA | CXL |
|---|---|---|
| 스코프 | 노드↔노드(network) | 노드 내(bus) |
| 메모리 모델 | 원격 메모리를 메시지로 읽고씀(통신) | 자기 주소공간처럼 load/store(공유) |
| 캐시 일관성 | 없음 | 있음 |
| 지연 | µs급 | ns급 |
| 용도 | 메모리 확장·풀링·일관 공유 |
- 보완 관계: 노드 간=RDMA, 노드 내 메모리 확장/풀링=CXL. CXL은 2024~26 본격 등장하는 신흥 기술.

### 11.6 NVL72
- 한 랙에 GPU 72개(+CPU)를 여러 컴퓨트 트레이에 담고 **NVSwitch/NVLink 패브릭으로 전부 직결**한 단일 시스템("한 랙짜리 AI 슈퍼컴퓨터").
- 핵심: GPU 72장이 **노드 경계 없이 하나의 NVLink 도메인 + 통합 메모리 공간**처럼 동작. 8장 단위로 끊기던 NVLink 도메인을 72장으로 확장.
- OpenShift 관점: NVL72 = 단일 노드가 아니라 **트레이마다 RHCOS를 올린 다수의 OCP 워커 노드 집합**. NVLink 패브릭은 OS/노드 경계와 무관하게 GPU를 묶음.
- 확장: 여러 NVL72 랙을 InfiniBand(RDMA)로 연결 → 총 "72 × 랙 수" GPU. 구조 = 랙 안 NVLink + 랙 간 RDMA(2단 계층).
- 구성요소: CPU+GPU(연산) + NVSwitch 패브릭(정체성) + 대량 HBM(메모리) + 액체냉각·통합전력(밀도 인프라).

### 11.7 SLI (역사 참고)
- 게이밍용 멀티GPU 기술(프레임 렌더링 분담, AFR). 메모리 합쳐지지 않음 → 딥러닝 분산과 다른 계보.
- 2080 Ti(튜링) 세대 즈음 SLI 브리지가 NVLink 브리지로 전환되며 무게중심이 게이밍→컴퓨팅으로 이동, 소비자용 SLI는 사실상 퇴장.

---

## 12. 모니터링 & 책임있는 AI
- **TrustyAI**: Red Hat 오픈소스 책임있는 AI 툴킷 — 드리프트 감지, 편향·공정성, 설명가능성(XAI), LLM 평가.
- Prometheus/Grafana/Loki와 결합해 ML 관측을 표준 클라우드 네이티브 옵저버빌리티에 통합. 임계치 초과 시 재학습 트리거.

## 13. 공급망 보안 (모델까지 확장)
- SonarQube, black/flake8/pylint(코드 품질), kube-linter, **StackRox/ACS**(취약점 스캔), **modelscan**(pickle 역직렬화 공격 등 모델 스캔), Sealed Secrets, **Sigstore/cosign**(서명), **Syft**(SBOM).
- 모델을 OCI 이미지(modelcar)로 만들면 일반 컨테이너처럼 스캔·서명·SBOM 적용 가능 → "모델도 공급망 아티팩트".

---

## 14. RHOAI 3.4 기능 (참고 — 상태는 릴리스마다 변동)

### GA (프로덕션 준비)
Model Registry, AI Pipelines(DSPA), MLflow Operator, TrustyAI, MaaS, NeMo Guardrails, MLServer ServingRuntime, Distributed Inference(llm-d), Llama Stack, KubeRay, Model Catalog, OCI ModelCar, Kubeflow Trainer v2, Workbench Images
- MaaS·NeMo Guardrails는 3.3 Tech Preview → 3.4 GA로 승격.
- OCI ModelCar: 대시보드에서 S3/URI 모델을 ModelCar 이미지로 변환·저장 기능 추가.

### Technology Preview (평가 중)
AutoML, AutoRAG, vLLM Runtime for MaaS, External OIDC for MaaS, MaaS Observability Dashboard, External Model Egress, Llama Stack Responses API, Workload Autoscaler(llm-d), Priority Flow Control(llm-d), Gateway Discovery(llm-d), Recommended vLLM Configs

### Developer Preview (실험적)
Advanced Model Catalog, Enhanced Pipeline UI, Custom Operator Support

> 정확한 최신 상태는 Red Hat 공식 릴리스 노트 및 "Supported Configurations" 문서에서 항목별 확인 필요.

---

## 15. 핵심 용어 빠른 사전
- **Workbench**: 코드 작성·대화형 실행·파이프라인 트리거용 IDE 파드(CR).
- **KFP / DSP**: ML 훈련 파이프라인 작성(SDK)+실행 엔진. Argo Workflows 백엔드.
- **Elyra**: Jupyter 내 비주얼 파이프라인 에디터(노트북 통째 연결).
- **Tekton**: k8s 네이티브 CI/CD 파이프라인(이벤트 반응·git·이미지·트리거).
- **Argo CD**: GitOps 배포 컨트롤러(git↔클러스터 reconcile).
- **Argo Workflows**: DAG 실행 엔진(KFP 백엔드). Argo CD와 별개.
- **KServe**: k8s 모델 서빙 표준(InferenceService).
- **Model Registry / Catalog / ModelCar**: 메타데이터 카탈로그 / 모델 진열장 / OCI 이미지 운반.
- **MLflow**: 실험 추적·모델 관리(오케스트레이션 아님).
- **Feast**: 피처 스토어(온라인/오프라인, skew 제거).
- **MaaS**: 중앙 LLM 서빙·거버넌스 플랫폼.
- **RAG / 임베딩 / 벡터 DB**: 검색 증강 생성 / 의미 보존 벡터화 / 유사 검색 저장소.
- **Ray / KubeRay**: 범용 분산 실행(학습·튜닝·데이터·추론).
- **Kueue**: 잡 큐잉(GPU 할당·우선순위·공정 공유).
- **MIG**: GPU 한 장을 최대 7개 하드웨어 격리 인스턴스로 분할.
- **NVLink / RDMA / InfiniBand / CXL**: 노드 내 GPU 직결 / 노드 간 직접 메모리 접근 / RDMA용 네트워크 / 노드 내 메모리 일관 공유.
- **NVL72**: NVLink 패브릭으로 72 GPU를 한 도메인으로 묶은 랙형 AI 슈퍼컴퓨터.

---

# 부록 A. 실무 보강 (구 `14-RHOAI-MLOps-파이프라인` 통합)

> 커리큘럼 노트 `14-RHOAI-MLOps-파이프라인`을 본 종합 문서로 통합(2026-06-16). OCP 엔지니어 관점의 실무 절차·전략 위주. 개념 본문(§1~15)과 함께 읽는다.

## A.1 모델 서빙 런타임 선택 (KServe ServingRuntime)

KServe는 여러 서빙 런타임을 지원한다. 모델 종류·요구사항으로 선택한다. (개념은 §6.4 KServe 참조)

| 런타임 | 특징 | 적합한 모델 |
|--------|------|-------------|
| **vLLM** | LLM 특화, 고성능 추론(PagedAttention·연속배치) | Llama, Granite 등 대형 LLM |
| **NVIDIA NIM** | NVIDIA 최적화 마이크로서비스 | NGC 카탈로그 모델 |
| **OpenVINO** | Intel 최적화, CPU 추론 | 경량 모델, CPU 환경 |
| **Triton** | 범용 추론 서버 | TensorFlow, PyTorch, ONNX |
| **TGIS/Caikit** | IBM 텍스트 생성 | IBM 계열 LLM |
| **Seldon MLServer** | 전통 ML 모델(V2 프로토콜) | scikit-learn, XGBoost 등 |

- vLLM 핵심 성능 지표: **TTFT**(첫 토큰까지), **TPOT**(토큰당 생성), **ITL**(연속 토큰 간 지연), **E2E Latency**(전체), **GPU KV Cache Usage**(캐시 사용률).
- 추론엔진 자체 비교(vLLM vs llama.cpp vs Ollama)·vLLM 튜닝 심화는 일반 AI 자료의 [[04-추론엔진-비교-가이드]] / [[05-vLLM-추론엔진-핵심정리]] 참조(폴더 4).

## A.2 NVIDIA NIM 통합

NIM(NVIDIA Inference Microservices)은 NVIDIA가 최적화한 추론 마이크로서비스 세트로 RHOAI에서 네이티브 지원.

**활성화 절차**
```
1. NVIDIA NGC 카탈로그에서 API 키 생성
2. RHOAI 대시보드(관리자) → NIM 활성화
3. 데이터 사이언스 프로젝트 생성
4. NIM 기반 모델 서빙 플랫폼 선택
5. 모델 배포 (예: meta-llama/Llama-3-8B-Instruct)
6. 외부 URL + 액세스 토큰 확인
7. OpenAI 호환 API로 호출
```

**호출 예시**
```python
from openai import OpenAI
client = OpenAI(base_url="https://<rhoai-외부-url>/v1", api_key="<액세스-토큰>")
response = client.chat.completions.create(
    model="meta-llama/Llama-3-8B-Instruct",
    messages=[{"role": "user", "content": "안녕하세요"}],
)
```
- 장점: NGC 카탈로그 모델을 별도 최적화 없이 즉시 서빙, 하이브리드 클라우드에서 일관된 추론 운영.

## A.3 미세조정(Fine-tuning) 전략

```
Full Fine-tuning   : 전체 파라미터 업데이트. 정확도 최고, GPU 메모리 많이(OOM 위험). 연산병목 환경에선 가장 빠름.
LoRA               : 작은 어댑터 행렬만 학습. 메모리 50%+ 절감, 더 큰 모델 가능. 연산병목 환경선 Full보다 느릴 수 있음.
QLoRA              : LoRA + 4-bit 양자화. 메모리 최소, 저사양 GPU로도 대형 모델. 양자화 오버헤드로 학습시간 최장.
```

| 상황 | 추천 |
|------|------|
| GPU 메모리 충분, 빠른 학습 | Full |
| 메모리 제한, 큰 모델 | LoRA |
| 메모리 매우 제한, 최대 절약 | QLoRA |
| 작업별 모델 변형 다수 | LoRA(어댑터 교체) |

**RHOAI 미세조정 스택**
- `fms-hf-tuning`(IBM Research): HF SFTTrainer 기반, PyTorch FSDP 지원, 컨테이너 이미지/Python 패키지.
- `TOPSAIL`: 버전별 성능 회귀 자동 감지.
- 실험(4×H100 80GB): 최신 RHOAI(2.17/2.18)가 2.16 대비 학습시간↓·처리량↑. QLoRA는 Mixtral 계열에서 LoRA 대비 VRAM 절반 이하.
- 양자화 방식 심화(W8A8/W4A16·LLM Compressor)는 [[03-LLM-모델-양자화-압축-핵심정리]] 참조(폴더 4).

## A.4 성능 검증: GuideLLM 부하 패턴

배포 전·플랫폼 업그레이드 후 성능 검증 필수. (도구 심화·에어갭·과포화는 [[06-LLM-벤치마킹-GuideLLM-가이드]] 폴더 4 참조)

| 패턴 | 입력 토큰 | 출력 토큰 | 특징 |
|------|-----------|-----------|------|
| 균일(Homogeneous) | 3072 고정 | 1200 고정 | 예측 가능, 테스트 용이 |
| 이질(Heterogeneous) | 평균 3072, 표준편차 2000 | 평균 512, 표준편차 1000 | 실제 운영 반영 |

- **핵심**: 균일 워크로드에서 잘 되는 설정이 이질에서 실패할 수 있다 → 반드시 이질 패턴도 검증.

## A.5 AI 자산 관리: Red Hat Developer Hub (RHDH/Backstage)

모델이 많아지면 "어떤 모델이 승인됐나?·이 API 어떻게 쓰나?"가 문제. RHDH AI 카탈로그가 해결.

```
Backstage 카탈로그
├── Component (type: model-server)  → vLLM/Ollama 기반 모델 서버
├── Resource  (type: ai-model)      → IBM Granite Code 8B, Llama 3 8B Instruct
└── API                             → OpenAI 호환 엔드포인트
```
```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: granite-model-server
  annotations:
    backstage.io/techdocs-ref: dir:.
spec:
  type: model-server
  lifecycle: production
  owner: ai-platform-team
```
- TechDocs로 제공: 모델 카드(학습데이터·성능·한계), 승인된 사용사례, API 키 발급법, curl/Python 예시, 윤리적 고려사항.

## A.6 Developer Sandbox 실습 환경

무료로 RHOAI 전체 스택 체험. 자원 제한: 프로젝트 1 / CPU 3코어 / RAM 14GB / 스토리지 40GB / 30일.

**자원 절약 팁**
- 파이프라인 서버가 MariaDB용 PVC 10GB 필요 → Workbench PVC를 20GB 대신 10GB로.
- 파이프라인 실험 전 Model Server를 0으로 스케일다운.
- Workbench 재생성 시 기존 PVC 재사용(데이터 유지).
- 샌드박스엔 S3 없음 → Minio를 컨테이너로 배포해 S3 호환 스토리지로.

## A.7 Apache Camel 통합: AI를 서비스로

모델 API를 기존 서비스와 통합하는 프레임워크.
```
AI 개발자:     데이터 수집 → 모델 학습 → 모델 배포 (OpenShift AI)
앱 개발자:     AI API 호출 → 비즈니스 로직 → 서비스 노출 (Apache Camel)
통합 흐름:     [외부 요청] → [Camel Route] → [RHOAI 모델 API] → [응답 처리] → [반환]
```
- 실습: Developer Sandbox + Dev Spaces(웹 VS Code)에서 로컬 설치 없이 가능.

*부록 A 참고 소스: 98-Wiki-Raws/0409-ai-study/platform 카테고리 PDF 16종 (구 14번 노트)*
