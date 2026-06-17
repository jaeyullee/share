# Kubeflow Trainer v2

> 프레임워크별 CRD(PyTorchJob/TFJob/MPIJob…)를 **단일 `TrainJob` + 재사용 런타임 템플릿**으로 통합한 차세대 학습 오퍼레이터. 3.4에서 GA(2.1.0).
> 영역: [20-분산워크로드-관계](20-분산워크로드-관계.md)

---

## 1. 정의 / 역할
- v1 Training Operator는 프레임워크마다 별도 CRD(`PyTorchJob` 등)를 썼다. v2는 이를 **`TrainJob`(무엇) + `TrainingRuntime`(어떻게)** 둘로 분리·통합.
- 선언적·재현 가능한 1회성 분산 학습 잡에 강함(Ray의 상주 cluster와 대비).

## 2. 버전 / 라이프사이클
- 업스트림: **`kubeflow/trainer`** (2.1.0). 3.2 TP → 3.3 GA → 3.4 GA.
- v1 (`kubeflow/training-operator` 1.9.0, PyTorchJob 등) = **Deprecated**(2.25부터).

## 3. 아키텍처 (파드=잡)
- **컨트롤 플레인(상주)**: 단일 Trainer controller-manager. TrainJob을 watch → 참조 런타임과 병합 → **JobSet으로 렌더링**(직접 파드 생성 ✗, JobSet에 위임).
- **데이터 플레인(잡별)**: 렌더된 JobSet → child Job → 학습 파드. **Pod 자체가 작업 단위**(Ray식 2층 스케줄러 없음). Pod끼리는 NCCL/gloo 등 **프레임워크 자체 통신**으로 그래디언트 교환, torchrun이 Pod 안에서 학습 프로세스 직접 기동.

## 4. CRD (group **`trainer.kubeflow.org/v1alpha1`**)

| CRD | Scope | 역할 |
|---|---|---|
| **TrainJob** | Namespaced | 데이터 사이언티스트가 제출하는 실제 학습 잡 |
| **TrainingRuntime** | Namespaced | 재사용 런타임 템플릿(네임스페이스) |
| **ClusterTrainingRuntime** | Cluster | 재사용 런타임 템플릿(클러스터 전역) |

> 주의: 출시 API는 `v1alpha1`(설계 제안서의 `v2alpha1` 아님).

### TrainJob 핵심 spec
- `runtimeRef`(`name`/`apiGroup`(기본 trainer.kubeflow.org)/`kind`) — 어떤 런타임을 쓸지.
- `trainer`(`image`/`command`/`args`/`env`/`numNodes`/`numProcPerNode`/`resourcesPerNode`).
- `initializer`(`dataset`/`model` — 각 `storageUri`/`secretRef`).
- `runtimePatches` — 런타임 JobSet 오버라이드(구조화 패치).
- `suspend`, `managedBy`(기본 `trainer.kubeflow.org/trainjob-controller`).

> 명칭 주의: `datasetConfig`/`modelConfig`/`podSpecOverrides`가 아니라 **`initializer.dataset`/`initializer.model`/`runtimePatches`**.

### TrainingRuntime 핵심 spec (공유 `TrainingRuntimeSpec`)
- `mlPolicy`(`numNodes` + `torch`/`mpi`/`jax`/`xgboost` 소스).
- `podGroupPolicy`(gang: coscheduling/volcano).
- **`template`** = `JobSetTemplateSpec`(내부가 `jobset.x-k8s.io/v1alpha2`의 JobSetSpec).

## 5. 템플릿 vs 잡 분리 (★Kustomize base/overlay 모델)
- **Runtime(템플릿)**: 플랫폼 엔지니어 소유. 이미지·노드 토폴로지·gang 정책을 JobSet 기반으로 한 번 정의, 재사용.
- **TrainJob(잡)**: 데이터 사이언티스트 소유. `runtimeRef`로 런타임 참조 + `trainer`/`initializer`/`runtimePatches`로 필요한 것만 오버라이드.

## 6. JobSet 사용 (하부 엔진)
```
TrainJob (runtimeRef + 오버라이드)
  └► Runtime (template=JobSetSpec) ──[Trainer가 mlPolicy 적용 + runtimePatches 병합]──►
       구체화된 JobSet ──► JobSet 컨트롤러 ──► child Job ──► Pod(학습 컨테이너)
```
- **JobSet** (`jobset.x-k8s.io/v1alpha2`, kubernetes-sigs/jobset): 여러 Job을 하나의 단위로 관리. `replicatedJobs[]`, `network`(headless Service + 안정 DNS `<job>-<idx>-<idx>.<subdomain>`), `successPolicy`/`failurePolicy`/`startupPolicy`, `suspend`.
- 가치: 멀티노드 학습 파드에 **stable network identity**(rendezvous/`MASTER_ADDR`/all-reduce)와 조율된 갱 라이프사이클 제공. Trainer는 ML 시맨틱에 집중, 다중 Job 오케스트레이션·네트워킹·실패 처리는 JobSet에 위임.

## 7. Kueue 연동
- TrainJob에 `queue-name` 라벨 → webhook이 `suspend: true` → admit 시 unsuspend.
- **MultiKueue**: 관리 클러스터에서 `managedBy`를 `kueue.x-k8s.io/multikueue`로 설정 → Trainer가 관리 클러스터 파드 생성을 건너뛰고 워커 클러스터로 디스패치(이중 실행 방지).

## 8. 동작 end-to-end
1. 사용자가 TrainJob 제출(runtime 참조, queue-name 라벨). suspend.
2. Trainer가 Runtime+TrainJob → JobSet 렌더(suspend).
3. Kueue가 Workload로 쿼터·갱 판정 → admit → unsuspend.
4. JobSet → Job → 학습 Pod×N 생성 + headless Service(stable DNS).
5. 각 Pod에서 torchrun 분산 학습 → 끝나면 Pod 종료(파드=잡 수명).

## 9. 운영 함정
- v1(PyTorchJob 등) deprecated → 신규는 TrainJob+Runtime. 단 일부 공식 예제가 여전히 v1 기반이라 문서 버전 혼동 주의.
- JIT/주기 체크포인팅, S3/PVC 백엔드 등 부가 기능은 별도(3.4 GA 본체와 별개로 일부 신규).
- 부분 스케줄링 데드락(→ [21-Kueue](21-Kueue.md)).

## 10. 출처
- API 소스: https://github.com/kubeflow/trainer/tree/master/pkg/apis/trainer/v1alpha1
- 마이그레이션: https://www.kubeflow.org/docs/components/trainer/operator-guides/migration/
- JobSet: https://github.com/kubernetes-sigs/jobset/tree/main/api/jobset/v1alpha2
- JIT 체크포인팅: https://developers.redhat.com/articles/2026/05/21/guide-jit-checkpointing-kubeflow-trainer-openshift-ai
