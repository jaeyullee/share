# Data Science Pipelines (DSP)

> ML 워크플로를 정의→컴파일→스케줄→실행→추적하는 컴포넌트. Kubeflow Pipelines v2 + Argo Workflows 기반.
> 영역: [40-파이프라인실험-관계](40-파이프라인실험-관계.md)

---

## 1. 정의 / 역할
- KFP SDK로 Python 파이프라인 작성 → **IR(Intermediate Representation) YAML** 컴파일 → OpenShift에서 컨테이너화된 단계로 실행. 아티팩트는 S3, 계보는 MLMD로 추적.

## 2. 버전 / 라이프사이클
- 2계층: **`opendatahub-io/data-science-pipelines-operator`(DSPO)** + **`kubeflow/pipelines`(KFP 2.x)** + **Argo Workflows**(실행 엔진).
- DSP는 **KFP 2.x 기반("DSP 2.0")** — 2.9부터 v2 기본, **2.16부터 v1(Tekton 기반) 완전 제거**. → 3.4는 전적으로 v2.
- 버전(혼합): KFP 2.4.x(추정), Argo 3.6~3.7대. 라이프사이클 **GA**.
- **3.4: `DataSciencePipelinesApplication`의 `v1alpha1` API 제거, 안정 `v1`만**.

## 3. 아키텍처 (네임스페이스 단위 독립 스택)
- **컨트롤 플레인(상시)**: API Server / Persistence Agent / ScheduledWorkflow Controller / Argo Workflow Controller(네임스페이스 스코프) / MLMD(gRPC+Envoy) / (옵션) MLpipeline UI / (옵션·비프로덕션) MariaDB·MinIO.
- **데이터 플레인(동적)**: run 트리거 시 Argo Workflow 생성 → 각 단계가 **Pod**로 실행. KFP v2는 단계 Pod에 **driver**(메타데이터/계보/캐시) + **launcher**(사용자 컨테이너 + 아티팩트 I/O) 컨테이너 관여.

## 4. CRD: DataSciencePipelinesApplication (DSPA)

| 항목 | 값 |
|---|---|
| group/version | `datasciencepipelinesapplications.opendatahub.io/v1` |
| kind / scope | `DataSciencePipelinesApplication` / **Namespaced** |

이 CR 하나가 네임스페이스의 DSP 스택 전체를 선언.
- 주요 spec: `dspVersion`(v2), `apiServer`(image/cacheEnabled/argoLauncherImage/argoDriverImage), `persistenceAgent`, `scheduledWorkflow`, `mlmd`, `workflowController`, `mlpipelineUI`, **`database`**(`mariaDB` 내장 ↔ `externalDB`, 상호배타), **`objectStorage`**(`minio` 내장 ↔ `externalStorage`, 상호배타), `podToPodTLS`.

## 5. DSPA가 배포하는 것
ds-pipeline API Server / Persistence Agent / ScheduledWorkflow Controller / **Argo Workflow Controller + argoexec** / MLMD gRPC(+Envoy) / (옵션) MariaDB / (옵션) MinIO / kube-rbac-proxy 사이드카. 런타임엔 driver·launcher 이미지가 단계 Pod에서 추가 사용.

## 6. 실행 모델
```
KFP SDK 정의 → 컴파일러가 IR YAML → API Server 업로드
   → 백엔드가 Argo Workflow 리소스로 변환 → Argo Controller가 DAG 오케스트레이션
   → 각 컴포넌트를 개별 Pod로 스케줄 → 아티팩트 S3 버킷 저장
```
v1(Tekton)→v2(Argo) 전환은 2.16에서 완료.

## 7. 연동
- **Workbench**: Elyra(JupyterLab)로 노트북을 파이프라인화해 API Server에 제출 → [42-Workbenches](42-Workbenches.md).
- **Object Storage**: 아티팩트 저장(필수 의존).
- **Model Registry**: 배포 대상 모델 등록(자동 통합 세부는 미확인).

## 8. 운영 함정
- v1/`v1alpha1` 완전 제거(마이그레이션 필수).
- **내장 Argo는 비지원**(별도 Argo 설치 시 충돌).
- 오브젝트 스토리지 필수, **내장 MinIO/MariaDB는 비프로덕션·비지원**(외부 S3/DB 권장).
- MySQL 8.4+는 `mysql_native_password` 수동 활성화.

## 9. 출처
- DSPO: https://github.com/opendatahub-io/data-science-pipelines-operator
- KFP: https://github.com/kubeflow/pipelines
- RHOAI 3.4 working_with_data_science_pipelines

## 10. 미확인/주의
- KFP/Argo/DSPO 정확 점버전, driver/launcher 세부는 KFP v2 일반 동작 기반 일부 추정.
