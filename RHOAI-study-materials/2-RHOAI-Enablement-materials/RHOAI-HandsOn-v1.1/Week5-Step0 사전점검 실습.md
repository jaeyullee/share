# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - LLM MLOps CI/CD 사전점검

> **환경별 재확인**: Operator version, GPU·메모리, StorageClass, 내부 registry/Nexus/S3/Git endpoint와 image digest는 검증 환경 값이다. Step1 전에 대상 환경의 대응 값을 표로 기록한다. 공통 경계 조건은 [실습자료 검토 항목](<00-실습자료-검토항목.md#환경별-재확인>)을 참고한다.

> 사전 활성화: [Week1 Day1&2](<Week1-Day1&2-환경구성.md>)의 AI Pipelines, Model Registry, KServe Standard, GPU/Trainer 구성과 [Tekton CI/CD와 Argo CD GitOps 구성](<Week1-Day1&2-환경구성.md#tekton-cicd와-argo-cd-gitops-구성>)을 확인하고 [Week3 Day11](<Week3-Day11 실습.md>)의 GPU를 정상화한다. Kueue를 사용할 경우 [Week3 Day12](<Week3-Day12 실습.md>)를 먼저 수행한다.

Tekton CI, KFP, Kubeflow Trainer v2, Model Registry, OpenShift GitOps와 KServe vLLM을 역할별로 연결한다. 운영형 흐름은 다음과 같다.

```text
Gitea push
  -> Tekton: 검증, training image build/push, KFP manifest compile
  -> Argo CD: Pipeline/PipelineVersion 동기화
  -> KFP: TrainJob 실행, metrics 수집, Model Registry Staging 등록
  -> Tekton promotion gate: Registry 상태와 지표 확인
  -> Argo CD: staging/production KServe vLLM 배포
```

### 기능 범위

| 기능 | 이 실습의 사용 방식 |
|---|---|
| OpenShift Pipelines | 소스 검증, Buildah 이미지 빌드, KFP manifest 발행, 승격 gate |
| RHOAI AI Pipelines | ML workflow와 Run, artifact, scalar metrics 관리 |
| Kubeflow Trainer v2 | 단일 GPU LoRA TrainJob 실행 |
| Model Registry | 모델 버전, S3 URI, Git commit, 지표와 stage 기록 |
| OpenShift GitOps | KFP 정의와 KServe 선언 상태 동기화·self-heal |
| KServe Standard vLLM | staging/production OpenAI 호환 API |

RHOAI 3.4에서 Kubeflow Trainer v2는 GA다. 설치된 `training-hub-th05-cuda128-torch29-py312`는 deprecated이므로 사용하지 않고 `torch-distributed-cuda130-torch210-py312`와 커스텀 LoRA image를 사용한다. MaaS 자체는 GA지만 MaaS에서 vLLM runtime을 직접 사용하는 기능은 TP이므로 운영 기본 경로에서 제외한다.

### 단일 GPU 랩 보정

현재 GPU worker의 물리 GPU가 1개이므로 훈련과 서빙을 동시에 실행하지 않는다.

1. KFP Run과 TrainJob을 완료한다.
2. TrainJob Pod가 종료돼 GPU가 반환됐는지 확인한다.
3. staging InferenceService를 배포하고 검증한다.
4. staging을 삭제한 뒤 production을 배포한다.

고객 운영환경은 training GPU pool과 serving GPU pool, staging과 production Namespace 또는 cluster를 분리한다.

### 설치 상태 확인

```bash
oc get dsc default-dsc -o json | jq '.spec.components | {
  trainer: .trainer.managementState,
  aipipelines: .aipipelines.managementState,
  kserve: .kserve.managementState,
  modelregistry: .modelregistry.managementState,
  kueue: .kueue.managementState
}'

oc get crd \
  trainjobs.trainer.kubeflow.org \
  clustertrainingruntimes.trainer.kubeflow.org \
  pipelines.pipelines.kubeflow.org \
  pipelineversions.pipelines.kubeflow.org \
  applications.argoproj.io

oc get clustertrainingruntime \
  torch-distributed-cuda130-torch210-py312

oc get packagemanifest openshift-pipelines-operator-rh \
  -n openshift-marketplace

oc get node ocp-w01-gpu \
  -o jsonpath='{.status.allocatable.nvidia\.com/gpu}{"\n"}'
```

GPU allocatable은 최소 `1`이어야 한다. `OpenShift Pipelines`는 Step 2에서 설치하므로 현재 `Pipeline`과 `EventListener` CRD가 없어도 된다.

### 실습 자산 확인

공개 커리큘럼 저장소의 `RHOAI-HandsOn-v1.1` 디렉터리에서 실행한다. 다른 위치에서 실행한다면 `RHOAI_HANDSON_DIR`에 해당 디렉터리의 절대경로를 지정한다.

```bash
cd /tmp/python3
export RHOAI_HANDSON_DIR="$PWD"
test -d "$RHOAI_HANDSON_DIR/models/llm-mlops"
test -f "$RHOAI_HANDSON_DIR/datasets/llm-support-sft/train.jsonl"

python "$RHOAI_HANDSON_DIR/models/llm-mlops/validate_dataset.py" \
  "$RHOAI_HANDSON_DIR/datasets/llm-support-sft/train.jsonl"
```

외부 `week5-*.yaml` 파일은 사용하지 않는다. 필요한 리소스 선언은 각 Step 문서의 heredoc에 포함되어 있다. 예상 출력은 `valid_rows=24`이며, 데이터는 운영 지원 질의응답 형식의 합성 데이터로 고객정보를 포함하지 않는다.

### 공식 문서

- [OpenShift Pipelines 1.22](https://docs.redhat.com/en/documentation/red_hat_openshift_pipelines/1.22/html/about_openshift_pipelines)
- [RHOAI 3.4 AI Pipelines](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/working_with_ai_pipelines/)
- [RHOAI 3.4 Kubeflow Trainer v2](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/working_with_distributed_workloads/working_with_distributed_workloads)
- [RHOAI 3.4 KServe vLLM](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/deploying_models/deploying_models)
- [OpenShift GitOps 1.21](https://docs.redhat.com/en/documentation/red_hat_openshift_gitops/1.21/html/argo_cd_instance/argo-cd-cr-component-properties)
