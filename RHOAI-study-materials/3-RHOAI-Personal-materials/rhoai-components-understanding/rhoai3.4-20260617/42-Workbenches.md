# Workbenches (Notebooks)

> 브라우저 기반 격리 컨테이너 IDE. 데이터 준비·모델 개발·학습 수행. JupyterLab(기본)/code-server/RStudio(TP).
> 영역: [40-파이프라인실험-관계](40-파이프라인실험-관계.md)

---

## 1. 정의 / 역할
- 데이터 사이언티스트가 노트북에서 대화형으로 실험하는 inner loop의 공간. RHOAI 진입점.

## 2. 버전 / 라이프사이클 (★두 컨트롤러 협력)
- **Kubeflow Notebook Controller (KF NC)** — `kubeflow/kubeflow`(→`kubeflow/notebooks`). `Notebook` CR → StatefulSet/Service + 컬링.
- **ODH Notebook Controller (ODH NC)** — `opendatahub-io/kubeflow`. OpenShift 통합: 인증 프록시 사이드카 주입 + 외부 노출 + TLS + NetworkPolicy.
- 버전 1.10.0(Workbenches), 라이프사이클 GA.

## 3. 아키텍처
- **컨트롤 플레인**(`redhat-ods-applications`): KF NC가 `notebooks.kubeflow.org` watch → StatefulSet(replicas 1)+Service; ODH NC가 mutating webhook으로 프록시 주입 + 외부 노출.
- **데이터 플레인**: Notebook Pod(IDE 컨테이너 + 인증 프록시 사이드카), PVC, Service, 외부 경로.
- **아키텍처 전환 중**: 전통 **Route + oauth-proxy** → 신 **Gateway API HTTPRoute + kube-rbac-proxy**(path-based). 3.4 기본/opt-in 여부 미확인(마이그레이션 권고 단계).

## 4. CRD: Notebook

| 항목 | 값 |
|---|---|
| group/version | `kubeflow.org/v1` |
| kind / scope | `Notebook` / Namespaced |

- `spec.template.spec`에 표준 **PodSpec** 임베드(containers/image/resources/tolerations/nodeSelector).
- RHOAI 어노테이션: `notebooks.kubeflow.org/last-activity`(컬링 판단), `kubeflow-resource-stopped`(정지→replicas 0), `notebooks.opendatahub.io/inject-auth`(프록시 주입).

## 5. 생성 리소스
StatefulSet(replicas 1) → Pod(**IDE 컨테이너 + 인증 프록시 사이드카**) + Service + **외부 경로(Route 또는 HTTPRoute)** + PVC + NetworkPolicy/TLS Secret.

## 6. 동작 end-to-end
1. Dashboard에서 Create workbench(이미지·하드웨어프로파일·스토리지 선택).
2. `Notebook` CR 생성 → ODH NC webhook이 프록시 주입 → KF NC가 StatefulSet+Service 생성.
3. Pod 기동(Stopped→Starting→Running) → 외부 경로 생성.
4. "Open" 시 인증 프록시가 OpenShift 인증/인가(kube-rbac-proxy는 SubjectAccessReview로 Notebook `get` 검증) → IDE 접속.

## 7. 컬링 (Idle 정지)
- KF NC가 `last-activity` 갱신 → idle 임계 초과 시 `kubeflow-resource-stopped` 부여 → **replicas 0(삭제 아님)**.
- 설정: Dashboard Cluster settings → Idle workbench timeout; ConfigMap **`notebook-controller-culler-config`**(`ENABLE_CULLING` 기본 **`false`**, `CULL_IDLE_TIME`).

## 8. 하드웨어/액셀러레이터 프로파일
- **Hardware Profiles: 3.4 GA** — accelerator profiles 대체. CPU/메모리·GPU 식별자·nodeSelector·tolerations 정의 → `Notebook` CR `spec.template.spec`에 반영. → [71-GPU-하드웨어프로필](71-GPU-하드웨어프로필.md)
- Accelerator Profiles + Container Size selector: 3.0부터 Deprecated.
- 3.4: `oc`로 워크벤치 fine-grained 커스텀 role 정의 가능.

## 9. 이미지 / 연동
- 이미지: `registry.redhat.io/rhoai/odh-workbench-*-py312-rhel9`(Minimal/DataScience/PyTorch/TensorFlow/TrustyAI/CodeServer/LLM-Compressor; CUDA·ROCm 변형).
- **3.4: MLflow SDK 사전설치**(datascience/tensorflow/pytorch/codeserver) → [43-MLflow](43-MLflow.md).
- Elyra(JupyterLab만)로 DSP 파이프라인 제출 → [41-Data-Science-Pipelines](41-Data-Science-Pipelines.md).
- Feature Store 연동(`feature_store.yaml` 자동 마운트) → [53-Feature-Store-Feast](53-Feature-Store-Feast.md).

## 10. 운영 함정
- 정지≠삭제(CR/PVC 잔존). 컬링 기본 OFF.
- 프록시 아키텍처 전환: 커스텀 이미지는 `NB_PREFIX` 처리 필요(oauth-proxy 하드코딩 시 리다이렉트 루프).
- storage class 변경 불가.

## 11. 출처
- KF NC: https://github.com/kubeflow/kubeflow (notebook-controller)
- ODH NC: https://github.com/opendatahub-io/kubeflow
- RHOAI 3.4 working_in_your_data_science_environment

## 12. 미확인/주의
- 3.4 프록시 기본값, 컬링 기본 timeout 수치, 컨트롤러 정확 태그.
