# Model Registry

> 모델 메타데이터의 **중앙 저장소**. 모델을 register/version/lifecycle 관리. "실험과 서빙 사이의 다리". **passive metadata store**(능동 오케스트레이션 안 함).
> 영역: [50-모델거버넌스-관계](50-모델거버넌스-관계.md)

---

## 1. 정의 / 역할
- 모델 메타데이터를 register/version/추적. control plane이 아니라 **수동 메타데이터 저장소**.

## 2. 버전 / 라이프사이클
- 업스트림 **`kubeflow/model-registry`**, RH 포크 `opendatahub-io/model-registry` + `model-registry-operator`.
- 컴포넌트 **GA**. 업스트림↔3.4 정확 매핑 미확인(0.3.x 추정).

## 3. 아키텍처
- **REST/OpenAPI 서버**(Go)가 1차 인터페이스. REST 경로 `/api/model_registry/v1alpha3/...` (이 v1alpha3는 **REST API 버전**, K8s CRD 버전과 별개).
- 코어 로직 → 데이터스토어 → **RDBMS(GORM)** 직접 접근.
- **gRPC 노출 없음. REST-only**(구 MLMD 시절 gRPC 제거).

## 4. CRD: ModelRegistry

| 항목 | 값 |
|---|---|
| group | `modelregistry.opendatahub.io` |
| kind / scope | `ModelRegistry`(`mr`) / **Namespaced** |
| versions | `v1alpha1`(deprecated) → **`v1beta1`(storage)** |

- 핵심 spec: `rest`(image/port/serviceRoute), `grpc`(**deprecated**), **`mysql`/`postgres`**(둘 중 하나 필수, 상호배타), `oauthProxy`/`kubeRBACProxy`(v1beta1에서 동시 사용 불가), `istio`(v1alpha1에만).
- **백엔드 DB**: **PostgreSQL 16.x** + **MySQL(최소 5.x, 9.x 권장)**. **MariaDB 미명시 → 지원 가정 금지**. 내장 기본 DB는 **테스트 전용**.

## 5. CR이 배포하는 것
operator가 REST 서버 **Deployment**(`rest-container` + 조건부 `kube-rbac-proxy`, 별도 MLMD/gRPC 컨테이너 없음) + Service + 선택 Route + 프록시. 외부 PG/MySQL 연결. operator는 `redhat-ods-applications`, 레지스트리는 **`rhoai-model-registries`** 네임스페이스.

## 6. 데이터 모델 (내부 ERD)
```
RegisteredModel (1) ──< ModelVersion (N) ──< ModelArtifact {uri}
                                          └─< DocArtifact
ServingEnvironment (= namespace) ──< InferenceService(엔티티) ──< ServeModel
```
- RegisteredModel(최상위 논리 모델) / ModelVersion(버전) / ModelArtifact(실제 파일, **uri 보유**) / ServingEnvironment(≈namespace) / InferenceService(레지스트리 측 메타데이터 엔티티, KServe CR과 동명이지만 별개) / ServeModel(서빙 이벤트).

## 7. 동작 end-to-end
- **UI**: AI hub → Registry → Register model(위치 S3/URI). 새 버전은 Versions 탭.
- **OCI ModelCar(3.4 신규)**: 등록과 동시에 S3/URI/`hf://` 소스를 OCI ModelCar 이미지로 변환 — **비동기 K8s Job**(Pending/Running/Complete/Failed).
- **REST/Python**: `register_model()`, `get_model_version()`, `get_model_artifact()`.

## 8. KServe 연동 ("레지스트리에서 배포")
배포 위저드: project 선택 → 매칭 connection 스캔 → serving 위저드. 생성된 **InferenceService**가 라벨로 레지스트리에 역링크(`modelregistry.kubeflow.org/registered-model-id` 등). 두 경로:
1. **직접**: `ModelArtifact.uri` → `InferenceService.spec.predictor.model.storageUri`.
2. **CSI(간접)**: `storageUri: model-registry://{model}/{version}` 포인터를 storage initializer가 resolve.
→ [31-KServe](31-KServe.md). 3.4 기본 경로는 미확인.

## 9. MLMD 제거 (확인)
**Google ML Metadata 의존성 제거됨**(업스트림 v0.3.0). 대체: **RDBMS(MySQL/PostgreSQL)에 GORM 직접 저장**. 아키텍처 문서의 "inspired by ML-Metadata"는 스키마 계보일 뿐 런타임 의존 아님.

## 10. 운영 함정
- 내장 DB 테스트 전용 → 프로덕션 외부 PG/MySQL.
- URI 등록 모델은 **public OCI repo만** 배포 가능.
- **live deployment 있는 모델은 archive 불가**(InferenceService 먼저 삭제).
- `v1alpha1` deprecated → v1beta1.
- **3.4부터 default group 자동생성 deprecated**(접근 그룹 수동 관리).
- 모델 서명/검증은 **TP**.

## 11. 출처
- CRD: `opendatahub-io/model-registry-operator .../crd/bases/modelregistry.opendatahub.io_modelregistries.yaml`
- 데이터모델: `kubeflow/model-registry .../api/openapi/model-registry.yaml`
- RHOAI 3.4 managing_model_registries

## 12. 미확인/주의
- 업스트림 정확 버전, MLMD 제거 정확 RHOAI 버전 경계, 기본 KServe 연동 경로, MariaDB.
