# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 5 - Step 6 TrainJob, 지표와 Model Registry 검증

> 사전 활성화: [Week5 Step 5](<Week5-Step5 실습.md>)에서 KFP Run의 `train-model` 단계가 시작된 것을 확인한다.

KFP component가 Kubeflow Trainer v2 TrainJob을 생성하고 기다리는 구조를 관찰한다. 학습 Pod가 직접 KFP component 안에서 실행되는 것이 아니라 Trainer controller가 JobSet과 GPU Pod를 관리한다.

### TrainJob과 GPU Pod 추적

```bash
oc get trainjob -n rhoai-llm-mlops -w
```

다른 Bastion 터미널에서 실행한다.

```bash
TRAINJOB=$(oc get trainjob -n rhoai-llm-mlops \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[-1:].metadata.name}')

JOBSET=$(oc get jobset -n rhoai-llm-mlops -o json | \
  jq -r --arg trainjob "$TRAINJOB" \
  '.items[] | select(any(.metadata.ownerReferences[]?; .name == $trainjob)) | .metadata.name')

test -n "$JOBSET" && test "$JOBSET" != "null" || {
  echo "No active JobSet for TrainJob: $TRAINJOB"
  oc get trainjob "$TRAINJOB" -n rhoai-llm-mlops -o json | jq '.status.conditions'
  exit 1
}

oc get jobset "$JOBSET" -n rhoai-llm-mlops -o wide

oc get pod -n rhoai-llm-mlops \
  -l jobset.sigs.k8s.io/jobset-name="$JOBSET" \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.nodeName}{"\t"}{.spec.containers[0].resources.requests.nvidia\.com/gpu}{"\n"}{end}'
```

`app.kubernetes.io/part-of=week5-llm-mlops` 라벨은 TrainJob에만 설정한다. Trainer가 만든 Pod는 JobSet 이름으로 자동 부여되는 `jobset.sigs.k8s.io/jobset-name` 라벨과 TrainJob owner reference로 추적한다.

`No active JobSet`이 출력되면 먼저 TrainJob condition을 확인한다. `Complete=True` 또는 `Succeeded=True`면 학습 Pod와 JobSet이 정리된 정상 완료 상태이므로 아래 S3 산출물 확인으로 진행한다. 완료 전 상태인데도 JobSet이 없으면 Step 5의 KFP Run `train-model` task 로그와 Trainer controller 로그를 확인한다.

Pod는 `ocp-w01-gpu`에 배치되고 `nvidia.com/gpu=1`을 요청해야 한다. 학습 log를 확인한다.

```bash
TRAIN_POD=$(oc get pod -n rhoai-llm-mlops \
  -l jobset.sigs.k8s.io/jobset-name="$JOBSET" \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[-1:].metadata.name}')

oc logs -n rhoai-llm-mlops "$TRAIN_POD" -f
```

LoRA trainable parameter 수, step별 loss와 마지막 JSON metrics가 출력된다. 이 합성 dataset은 CI/CD 경로 검증용이므로 모델 품질을 대표하지 않는다.

### 완료 상태와 GPU 반환

```bash
TRAINJOB=$(oc get trainjob -n rhoai-llm-mlops \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[-1:].metadata.name}')

oc get trainjob "$TRAINJOB" -n rhoai-llm-mlops -o json | \
  jq '.status.conditions'

oc get jobset,pod -n rhoai-llm-mlops -o wide
```

`Complete` 또는 `Succeeded` condition이 True가 되면 KFP component가 S3의 `metrics.json`을 읽고 다음 `register-model` 단계로 진행한다. 학습 Pod가 `Completed`이면 GPU request는 더 이상 scheduler의 가용량을 점유하지 않는다.

### S3 산출물과 지표 확인

```bash
TRAINJOB=$(oc get trainjob -n rhoai-llm-mlops \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[-1:].metadata.name}')

RUN_ID=$(oc get trainjob "$TRAINJOB" -n rhoai-llm-mlops \
  -o jsonpath='{.metadata.labels.mlops\.opendatahub\.io/git-commit}' | \
  cut -c1-12)

printf 'TrainJob=%s\nRun ID=%s\n' "$TRAINJOB" "$RUN_ID"

mc ls --recursive \
  truenas/rhoai-llm-mlops/models/support-assistant/$RUN_ID/

mc cat \
  truenas/rhoai-llm-mlops/models/support-assistant/$RUN_ID/metrics.json | \
  jq .
```

다음 항목을 확인한다.

- `model/`: LoRA adapter가 merge된 vLLM 서빙용 Transformers model
- `adapter/`: LoRA adapter와 checkpoint 정보
- `metrics.json`: source commit, dataset/base URI, `train_loss`, `train_runtime`, sample 수

### KFP Run과 metrics 확인

RHOAI 대시보드의 `rhoai-llm-mlops` 프로젝트에서 `Data Science Pipelines` -> `Runs`로 이동해 해당 Run을 연다.

1. `train-model` task가 성공했는지 확인한다.
2. `register-model` task가 성공했는지 확인한다.
3. 위 S3 `metrics.json`의 `train_loss`, `train_runtime`, `samples`를 기록한다.
4. 아래 Model Registry의 같은 Model Version custom properties에서 `train_loss`, `train_runtime`이 S3 값과 일치하는지 확인한다.

RHOAI 3.4 콘솔은 Run 그래프의 `Output artifacts`에서 `system.Metrics` metadata를 `-` 또는 빈 값으로 표시할 수 있다. 이는 KFP artifact 전달 또는 학습 실패를 의미하지 않는다. 이 실습의 지표 원본은 S3 `metrics.json`이고, `register-model`이 그 파일을 읽어 Model Registry custom property로 등록한다.

KFP Run 전체가 성공해야 다음 승격 단계로 진행한다.

### Model Registry 확인

RHOAI 대시보드에서 `AI hub` -> `Models` -> `Registry`로 이동해 기존 registry를 연다.

1. Registered Model `support-assistant`를 연다.
2. 이름이 `<SHORT_COMMIT>`인 Model Version을 연다.
3. Version 이름을 눌러 `Details` 탭에서 version metadata와 custom properties를 확인한다. 현재 RHOAI 3.4 콘솔은 이 API로 등록한 artifact URI를 표시하지 않으므로, 아래 CLI로 model location을 확인한다.
4. custom properties의 `stage=Staging`, `git_commit`, `train_loss`, `train_runtime`을 확인한다.

### Model Registry artifact URI CLI 확인

다음 명령은 Model Version의 artifact API에서 실제 등록 URI를 조회한다. port-forward는 명령 종료 시 정리한다.

```bash
bash <<'BASH'
set -euo pipefail

NAMESPACE=rhoai-llm-mlops
REGISTRY_NAMESPACE=rhoai-model-registries
REGISTRY_SERVICE=jukebox-registry
REGISTRY_PORT=18084
REGISTRY_API="http://127.0.0.1:${REGISTRY_PORT}/api/model_registry/v1alpha3"

cleanup() {
  kill "${PF_PID:-}" 2>/dev/null || true
  wait "${PF_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# The latest TrainJob is the source of truth for the source commit and Run ID.
TRAINJOB=$(oc get trainjob -n "$NAMESPACE" \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[-1:].metadata.name}')
FULL_COMMIT=$(oc get trainjob "$TRAINJOB" -n "$NAMESPACE" \
  -o jsonpath='{.metadata.labels.mlops\.opendatahub\.io/git-commit}')
RUN_ID=${FULL_COMMIT:0:12}

oc port-forward -n "$REGISTRY_NAMESPACE" \
  "svc/$REGISTRY_SERVICE" "${REGISTRY_PORT}:8080" \
  >/tmp/week5-registry-port-forward.log 2>&1 &
PF_PID=$!

for _ in {1..20}; do
  curl -fsS "$REGISTRY_API/registered_models?pageSize=1" >/dev/null 2>&1 && break
  sleep 1
done

REGISTERED_MODEL_ID=$(curl -fsS "$REGISTRY_API/registered_models?pageSize=100" | \
  jq -r '[.items[] | select(.name == "support-assistant") | .id][0] // empty')
MODEL_VERSION_ID=$(curl -fsS "$REGISTRY_API/model_versions?pageSize=100" | \
  jq -r --arg model_id "$REGISTERED_MODEL_ID" --arg run_id "$RUN_ID" \
    '[.items[] | select((.registeredModelId | tostring) == $model_id and .name == $run_id) | .id][0] // empty')

if [ -z "$REGISTERED_MODEL_ID" ] || [ -z "$MODEL_VERSION_ID" ]; then
  echo "ERROR: support-assistant/$RUN_ID Model Version을 찾지 못했습니다." >&2
  exit 1
fi

ARTIFACT_URI=$(curl -fsS \
  "$REGISTRY_API/model_versions/$MODEL_VERSION_ID/artifacts?pageSize=100" | \
  jq -r '[.items[] | select(.artifactType == "model-artifact") | .uri][0] // empty')
EXPECTED_URI="s3://rhoai-llm-mlops/models/support-assistant/$RUN_ID/model"

printf 'TrainJob=%s\nGit commit=%s\nRun ID=%s\nModel Version ID=%s\nArtifact URI=%s\n' \
  "$TRAINJOB" "$FULL_COMMIT" "$RUN_ID" "$MODEL_VERSION_ID" "$ARTIFACT_URI"

[ "$ARTIFACT_URI" = "$EXPECTED_URI" ]
printf 'Verified expected URI: %s\n' "$EXPECTED_URI"
BASH
```

위 명령이 성공하면 Run ID, Model Version, artifact URI가 모두 같은 source commit으로 연결된 것이다. 아래 명령은 위 검증이 실패했을 때만 API 목록과 중간 ID를 조사하는 troubleshooting 절차다.

```bash
oc port-forward -n rhoai-model-registries \
  svc/jukebox-registry 18084:8080 \
  >/tmp/week5-registry-port-forward.log 2>&1 &
PF_PID=$!
cleanup_registry_port_forward() {
  kill "$PF_PID" 2>/dev/null || true
  wait "$PF_PID" 2>/dev/null || true
}
trap cleanup_registry_port_forward EXIT INT TERM

REGISTRY_API=http://127.0.0.1:18084/api/model_registry/v1alpha3

REGISTERED_MODEL_ID=$(curl -fsS "$REGISTRY_API/registered_models?pageSize=100" | \
  jq -r '.items[] | select(.name == "support-assistant") | .id')

MODEL_VERSION_ID=$(curl -fsS "$REGISTRY_API/model_versions?pageSize=100" | \
  jq -r --arg model_id "$REGISTERED_MODEL_ID" --arg run_id "$RUN_ID" \
    '.items[] | select((.registeredModelId | tostring) == $model_id and .name == $run_id) | .id')

printf 'Registered Model ID=%s\nModel Version ID=%s\n' \
  "$REGISTERED_MODEL_ID" "$MODEL_VERSION_ID"

if [ -z "$REGISTERED_MODEL_ID" ] || [ "$REGISTERED_MODEL_ID" = "null" ] || \
   [ -z "$MODEL_VERSION_ID" ] || [ "$MODEL_VERSION_ID" = "null" ]; then
  echo "Model 또는 Version을 찾지 못했습니다. RUN_ID와 API 목록을 확인합니다."
  curl -fsS "$REGISTRY_API/model_versions?pageSize=100" | \
    jq -r '.items[] | [.id,.registeredModelId,.name] | @tsv'
else
  curl -fsS \
    "$REGISTRY_API/model_versions/$MODEL_VERSION_ID/artifacts?pageSize=100" | \
    jq -r '.items[] | select(.artifactType == "model-artifact") | .uri'
fi

cleanup_registry_port_forward
trap - EXIT INT TERM
```

출력이 `s3://rhoai-llm-mlops/models/support-assistant/<RUN_ID>/model`이면 올바르다.

Model Registry의 `state=LIVE`는 객체 생명주기이고 이 실습의 `stage=Staging/Production`은 배포 승인 단계를 나타내는 별도 custom property다.

### 확인 기준

- Trainer v2가 단일 GPU TrainJob을 완료했다.
- S3에 merged model, adapter와 metrics가 같은 Run ID 아래 존재한다.
- S3 metrics와 Model Registry custom property가 일치한다.
- Model Registry 버전의 Git commit, S3 URI와 지표를 source commit까지 추적할 수 있다.
- staging 서빙 전 학습 Pod가 종료되어 GPU가 반환됐다.
