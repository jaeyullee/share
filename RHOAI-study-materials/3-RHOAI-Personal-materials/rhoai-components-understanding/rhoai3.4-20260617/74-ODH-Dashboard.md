# ODH Dashboard + OdhDashboardConfig

> RHOAI/ODH의 **단일 웹 UI 진입점**. 모든 기능의 사용자 진입점이자, 피처 플래그로 노출을 게이팅하는 컨트롤러.
> 영역: [70-가속기데이터UI-관계](70-가속기데이터UI-관계.md)

---

## 1. 정의 / 역할
- 모노레포(React 18 + PatternFly v6 + Module Federation, Node/Express + 일부 Go BFF). `redhat-ods-applications` 네임스페이스.
- 워크벤치/서빙/파이프라인/distributed workloads/모델 카탈로그·레지스트리 등 모든 기능의 진입점.

## 2. CRD: OdhDashboardConfig (소스 확인)

| 항목 | 값 |
|---|---|
| group/version | `opendatahub.io/**v1alpha**` (★`v1alpha1` 아님) |
| kind / scope | `OdhDashboardConfig` / Namespaced |
| 싱글톤 | `odh-dashboard-config` @ `redhat-ods-applications` |

- **`opendatahub.io/managed: "false"`**: operator가 초기 1회 생성 후 **Unmanaged 전환** → 사용자 직접 편집, operator가 재조정/업그레이드로 덮어쓰지 않음.
- spec 최상위: `dashboardConfig`(피처 플래그), `groupsConfig`(read-only), `notebookSizes`(deprecated), `modelServerSizes`(deprecated), `notebookController`, `templateOrder`, `hardwareProfileOrder`, `modelServing`, `genAiStudioConfig`.

## 3. 제어 대상 (피처 플래그)
규칙: `disable*`는 **true=숨김, false=노출**. 주요: `disableModelServing`, `disableKServe(Auth/Metrics/Raw)`, `disablePipelines`, `disableDistributedWorkloads`, `disableModelCatalog`, `disableModelRegistry`, `disableKueue`, `disableLMEval`, `disableFeatureStore`, `disableLLMd`, `disableProjectScoped` 등. enable류: `genAiStudio`, `modelAsService`, `trainingJobs`, `vLLMDeploymentOnMaaS` 등(다수 TP).

### ★ Deprecated 플래그 (CEL로 변경 차단)
| 필드 | 상태 |
|---|---|
| `disableModelMesh` | DEPRECATED (ModelMesh 제거됨) |
| `disableAcceleratorProfiles` | DEPRECATED (HardwareProfile 대체) |
| **`disableHardwareProfiles`** | DEPRECATED — **GA라 더 이상 끌 수 없음** |
| `disableFineTuning`, `mlflow` | DEPRECATED |

→ 위 + `notebookSizes`/`modelServerSizes`는 CEL(`self == oldSelf`)로 **값 변경 시 admission 거부**.

## 4. 동작 메커니즘 ("areas" 시스템)
기능 가시성 = **AND 3조건**: ① DSC에 백엔드 컴포넌트 설치 ② OdhDashboardConfig 피처 플래그 활성 ③ 의존 area 설치.
- UI-K8s 기능(플래그만) vs UI-Backend 기능(플래그 + DSC `requiredComponents`).
- 상태는 DSC/DSCI `.status` + OdhDashboardConfig에서 읽음. **각 pod가 2분마다 캐시 갱신** → 편집 후 UI 반영 ~2분 지연.

## 5. 다른 CRD 생성/조회
- DS Project = OpenShift Project(별도 CRD 없음), Custom Images = ImageStreams.
- Notebooks(`kubeflow.org`) — `notebookController`가 제어 → [42-Workbenches](42-Workbenches.md).
- 모델 서빙 = KServe `InferenceService`/`ServingRuntime`, `spec.modelServing.deploymentStrategy`(rolling|recreate) → [31-KServe](31-KServe.md).
- HardwareProfile(`infrastructure.opendatahub.io/v1`) — 읽어 선택지로 제시, `hardwareProfileOrder`로 순서 → [71-GPU-하드웨어프로필](71-GPU-하드웨어프로필.md).

## 6. DSC 관계 + 3.4 UI 변경
- dashboard는 DSC `spec.components`의 컴포넌트(`managementState`). **UI 가시성(OdhDashboardConfig) + 백엔드 설치(DSC) 2층 구조** — 둘 다 충족해야 노출.
- 3.4: HardwareProfiles GA(끌 수 없음), MLflow GA(`mlflow` 플래그 불필요), MaaS GA, AI Available Assets 페이지 신설, Distributed Inference YAML 뷰어.

## 7. 운영 함정
- `v1alpha`(≠v1alpha1). 싱글톤 `odh-dashboard-config`/`redhat-ods-applications`.
- 편집 후 ~2분 지연. deprecated 필드 변경 admission 거부(`disableHardwareProfiles=true` 실패).
- `notebookSizes`/`modelServerSizes` 변경 잠김(→HardwareProfile로).
- `groupsConfig`는 `Auth` 리소스(`spec.adminGroups`/`allowedGroups`)로 설정.
- `managed:false`라 operator가 오편집 복구·업그레이드 덮어쓰기 안 함.

## 8. 출처
- 소스: `opendatahub-io/odh-dashboard` (manifests/.../odhdashboardconfigs...)
- ADR: `opendatahub-io/architecture-decision-records` (dashboard/configuringDashboard.md)
- RHOAI 3.4 managing_resources
