# DataScienceCluster (DSC) & DSCInitialization (DSCI)

> RHOAI를 켜는 **두 개의 클러스터 싱글톤 CR**. DSCI가 플랫폼 공통 기반을 먼저 깔고, DSC가 그 위에서 ML 컴포넌트를 토글한다.
> 영역: [10-플랫폼토대-관계](10-플랫폼토대-관계.md) · 짝: [11-RHOAI-Operator](11-RHOAI-Operator.md)

---

## 1. 두 CR 한눈에

| | DSCInitialization (DSCI) | DataScienceCluster (DSC) |
|---|---|---|
| api group | `dscinitialization.opendatahub.io` | `datasciencecluster.opendatahub.io` |
| version | v1, **v2(storage)** | v1, **v2(storage)** |
| scope | Cluster (싱글톤, `dsci`) | Cluster (싱글톤, `dsc`) |
| 역할 | 공통 기반 초기화 | 컴포넌트 토글 |
| 순서 | 먼저 | DSCI 이후(precondition) |

> 3.4는 v1·v2 공존 + **v2가 storage version**. WebFetch로는 v1만 보여 MLflow/Trainer가 없는 듯 보이나, **소스 확인 결과 v2에 존재**. v2가 실질 동작 기준.

---

## 2. DataScienceCluster (DSC)

### 2.1 v1 vs v2 컴포넌트 목록 차이 (3.4 핵심 변화)

| `spec.components.*` | v1 | v2 (3.4 기준) | 비고 |
|---|---|---|---|
| dashboard / workbenches / kserve | O | O | kserve는 RawDeployment만 |
| datasciencepipelines | O | **→ `aipipelines`로 rename** | v2 json 태그 변경 |
| ray / kueue / trustyai / modelregistry | O | O | |
| trainingoperator | O | O | Training Operator **v1(deprecated)** |
| feastoperator / llamastackoperator | O | O | |
| **modelmeshserving** | O | **제거됨** | ModelMesh deprecated |
| **codeflare** | O | **제거됨** | CodeFlare Operator 3.0 removed |
| **mlflowoperator** | ✗ | **신규** | 3.4 DSC managed 승격 |
| **trainer** | ✗ | **신규** | Kubeflow Trainer v2 |
| **sparkoperator** | ✗ | **신규** | Spark Operator (DP) |

→ **3.4 v2 토글 가능 컴포넌트 = 14개**: dashboard, workbenches, kserve, aipipelines, kueue, ray, trustyai, modelregistry, trainingoperator, **trainer**, feastoperator, llamastackoperator, **mlflowoperator**, **sparkoperator**.

### 2.2 managementState
- 대부분 컴포넌트: **`Managed` | `Removed`** 2값.
  - **Managed**: 오퍼레이터가 적극 관리(설치·유지·업그레이드).
  - **Removed**: 설치 안 함, 있으면 제거.
- 일부만 **`Unmanaged`** 추가(Kueue v1 타입, DSCI의 TrustedCABundle 등). Unmanaged = 생명주기는 관리 안 하되 보조 설정은 생성. → "Unmanaged가 전 컴포넌트 공통"은 부정확.

### 2.3 spec 패턴
- 각 컴포넌트 필드 = `DSC<Component>` 구조체 = `common.ManagementSpec`(managementState) + `<Component>CommonSpec`(튜닝) 인라인.
- 예) `DSCKserve` → `KserveCommonSpec`: `rawDeploymentServiceConfig`, `nim`(NVIDIA NIM), `modelsAsService`, `wva`(workload-variant-autoscaler).
- `status.components.<name>` + `releases[]`(name/version/repoUrl) — **실제 배포된 업스트림 버전이 status에 기록**.

### 2.4 reconcile 액션 체인 (소스 확정)
`initialize → checkPreConditions(DSCI 확인, 없으면 실패) → updateStatus → provisionComponents(enable된 컴포넌트 CR 생성) → deploy → gc(disable된 것 정리)`. 전체 준비는 `ComponentsReady` 조건으로 집계.

---

## 3. DSCInitialization (DSCI)

### 3.1 역할
플랫폼 공통 기반. DSC보다 **먼저** 존재해야 함(DSC preCondition이 조회). 보통 오퍼레이터 설치 후 기본 DSCI 생성.

### 3.2 spec 핵심 필드 (RHOAI 빌드 기준)
- **`applicationsNamespace`** (기본 `redhat-ods-applications`) — **immutable**(생성 후 변경 불가). RHOAI 컴포넌트가 깔리는 네임스페이스.
- **`monitoring`** — managementState + metrics/traces(Tempo)/alerting. 별도 `Monitoring` 서비스 CR(`default-monitoring`)로 구체화.
- **`serviceMesh`** — **RHOAI 빌드에만 존재**. ControlPlane(기본 `istio-system`). 구 KServe Serverless의 필수 선행조건이었으나 3.4 RawDeployment 기본화로 의존 약화. (v2 spec에는 serviceMesh 필드 미존재 — Serverless deprecation과 정합)
- **`trustedCABundle`** — managementState(`Managed/Removed/Unmanaged`, 기본 Removed) + customCABundle. Managed면 전 네임스페이스에 `odh-trusted-ca-bundle` ConfigMap 주입.
- **`devFlags`** — logLevel 등(개발용).

---

## 4. 플랫폼 서비스 CR (참고)
DSC/DSCI 외에 오퍼레이터가 관리하는 싱글톤 서비스 CR. group **`services.platform.opendatahub.io/v1alpha1`**, Cluster scope:
- **Auth** (`auth`) — 인증 통합(3.4 Direct OIDC 등).
- **Monitoring** (`default-monitoring`) — DSCI.monitoring 구체화(Prometheus/Tempo/OTel).
- **GatewayConfig** — Gateway API 진입점(도메인/OIDC). DSC가 도메인 변경 watch.

컴포넌트 CR group = **`components.platform.opendatahub.io/v1alpha1`** (Kserve, Trainer, MLflowOperator, ModelController 등, 전부 Cluster scope, 이름 `default-<component>` 고정).

### ModelController (내부 전용, 토글 불가)
- `components.platform.opendatahub.io/v1alpha1`, `default-modelcontroller`, Cluster scope.
- DSC `spec.components`에 노출 안 됨. KServe/ModelRegistry enable 상태에 따라 **DSC가 자동 생성**. 모델 서빙 공통 컨트롤러(NIM, WVA, ModelRegistry 연동).

---

## 5. ERD
```
DSCInitialization (싱글톤)
  ├─► applicationsNamespace, Monitoring CR, Auth CR, ServiceMesh, CA번들
  ▲ precondition
DataScienceCluster (싱글톤)
  └─(owns)► 컴포넌트 CR 14종 + ModelController(자동) + Tenant(MaaS)
              └─► 컴포넌트 컨트롤러 ─► 실제 Deployment/Service/CRD/RBAC
```

## 6. 운영 함정
- **DSCI 없으면 DSC 실패**(precondition). 설치 순서 중요.
- `applicationsNamespace`는 immutable — 처음에 잘 정해야 함.
- v1만 보고 "MLflow/Trainer 없다"고 오판 금지 — v2 storage version 기준.
- modelmeshserving/codeflare는 v1에만 잔존, v2 신규 배포엔 비노출.

## 7. 출처
- DSC v2: `red-hat-data-services/rhods-operator` `/api/datasciencecluster/v2/datasciencecluster_types.go`
- DSCI v2(rhoai): `/api/dscinitialization/v2/dscinitialization_types.rhoai.go`
- 컴포넌트 타입: `/api/components/v1alpha1/`
- DSC 컨트롤러: `/internal/controller/datasciencecluster/`

## 8. 미확인/주의
- DSCI v2의 ServiceMesh 변환 경로(v2→v1) 미확인.
- `managementState` 3값(Unmanaged)은 일부 필드 한정 — 컴포넌트별 확인 필요.
