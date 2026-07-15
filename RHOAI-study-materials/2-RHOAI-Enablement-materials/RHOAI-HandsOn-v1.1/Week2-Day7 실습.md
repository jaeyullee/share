# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day7

> 사전 활성화: [Week1 Day1&2 - AI Pipelines와 Model Registry 구성](<Week1-Day1&2-환경구성.md#ai-pipelines와-model-registry-구성>)과 같은 문서의 MinIO/S3 `routingViaHost` 구성을 먼저 확인한다.

Data Science Pipeline을 이용해서 전처리 -> 훈련 -> 평가 단계를 재사용 가능한 파이프라인으로 실행한다.
폐쇄망 실습이므로 Pipeline component에서 외부 PyPI나 GitHub에 접근하지 않는다.

### 파이프라인 입력 데이터 준비
```bash
ls /tmp/python3/datasets/fraud-credit/fraud_sample.csv

mc alias set truenas http://192.168.20.5:9000 \
  '<MINIO_ID>' '<MINIO_PW>'
mc mb --ignore-existing truenas/rhoai-pipelines
mc cp /tmp/python3/datasets/fraud-credit/fraud_sample.csv \
  truenas/rhoai-pipelines/input/fraud_sample.csv
mc stat truenas/rhoai-pipelines/input/fraud_sample.csv
```

### Pipeline Server용 S3 Secret 생성
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: aws-connection-pipelines
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    opendatahub.io/connection-type: s3
    openshift.io/display-name: pipelines-minio
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: <MINIO_ID>
  AWS_SECRET_ACCESS_KEY: <MINIO_PW>
EOF
```

### DataSciencePipelinesApplication 생성
`routingViaHost`는 cluster-wide 설정이므로 DSPA Operator와 Pipeline Pod 모두 노드의 storage 경로로 MinIO에 접근할 수 있다. S3 health check를 활성화한 상태로 DSPA를 만들고 실제 Pipeline importer와 artifact upload도 함께 검증한다.

```bash
oc apply -f - <<'EOF'
apiVersion: datasciencepipelinesapplications.opendatahub.io/v1
kind: DataSciencePipelinesApplication
metadata:
  name: dspa
  namespace: jukebox
spec:
  dspVersion: v2
  apiServer:
    pipelineStore: database
  database:
    mariaDB:
      deploy: true
      storageClassName: truenas-nfs
      pvcSize: 5Gi
  objectStorage:
    externalStorage:
      bucket: rhoai-pipelines
      host: 192.168.20.5
      port: "9000"
      scheme: http
      region: us-east-1
      s3CredentialsSecret:
        secretName: aws-connection-pipelines
        accessKey: AWS_ACCESS_KEY_ID
        secretKey: AWS_SECRET_ACCESS_KEY
EOF

oc get dspa dspa -n jukebox -w
```

`READY=True`가 되면 `Ctrl+C`로 종료한다.

### 폐쇄망 KFP compiler 준비
RHOAI 3.4 Data Science Workbench 이미지에는 KFP SDK 2.16.0이 포함되어 있다. 별도 Nexus/PyPI 설치 없이 기존 Workbench에서 컴파일하거나 다음 임시 compiler Pod를 사용한다.

```bash
oc run day07-compiler -n jukebox \
  --image=registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:19e62e604a6b74ded1c5df88112e5be44424fb1752df46dc1587447fe024865f \
  --command -- sleep infinity

oc wait --for=condition=Ready pod/day07-compiler \
  -n jukebox --timeout=300s
oc exec -n jukebox day07-compiler -- python -c \
  'import kfp; print(kfp.__version__)'
```

### 3단계 파이프라인 작성
`@dsl.component`는 실행 Pod에서 KFP package를 설치하려고 할 수 있다. 폐쇄망에서는 `@dsl.container_component`로 명령을 명시해서 runtime `pip install`을 제거한다. 단, `dsl.Metrics` 값은 일반 파일 내용이 아니라 KFP Artifact metadata로 전달해야 대시보드에서 scalar metric으로 표시된다. `evaluate`는 KFP executor output 파일에 metadata를 기록한다. 이 환경의 DSPA MariaDB는 컴파일된 `PipelineSpec` 안의 한글 바이트를 저장하지 못하므로, Pipeline Python 코드 내부 주석은 ASCII 영문으로 작성한다. 한글 주석이 포함되면 version 업로드가 HTTP 500과 MariaDB `Error 1366 Incorrect string value`로 실패한다.

```bash
cat > /tmp/python3/day07-pipeline.py <<'PY'
from kfp import compiler, dsl

# Pin the verified RHOAI runtime image for reproducible task environments.
IMAGE = (
    "registry.redhat.io/rhoai/"
    "odh-pipeline-runtime-datascience-cpu-py312-rhel9@"
    "sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661"
)

# Preprocess the source CSV and publish train/test Dataset artifacts.
PREPROCESS = r'''
import os, sys, pandas as pd
from sklearn.model_selection import train_test_split
source, train_path, test_path = sys.argv[1:4]
frame = pd.read_csv(source).dropna()
# Keep the split reproducible for a fair model comparison.
train, test = train_test_split(frame, test_size=0.2, random_state=42)
for path in (train_path, test_path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
train.to_csv(train_path, index=False)
test.to_csv(test_path, index=False)
print(f"train={len(train)} test={len(test)}")
'''

# Train a Random Forest and publish a Model artifact with lineage metadata.
TRAIN = r'''
import hashlib, json, os, sys, joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier
source, estimators, output, executor_input_json = sys.argv[1:5]
features = ["amount", "age", "tenure_months", "num_claims",
            "credit_score", "distance_km", "channel"]
frame = pd.read_csv(source)
model = RandomForestClassifier(n_estimators=int(estimators), random_state=42)
model.fit(frame[features], frame["label"])
# Save the serialized model at the artifact path supplied by KFP.
os.makedirs(os.path.dirname(output), exist_ok=True)
joblib.dump(model, output)
with open(output, "rb") as stream:
    model_sha256 = hashlib.sha256(stream.read()).hexdigest()

# Add the training parameters and digest to the KFP Model artifact metadata.
executor_input = json.loads(executor_input_json)
executor_output_path = executor_input["outputs"]["outputFile"]
model_artifact = executor_input["outputs"]["artifacts"]["model_out"]["artifacts"][0]
runtime_artifact = {
    "name": model_artifact["name"],
    "uri": model_artifact["uri"],
    "metadata": {
        "framework": "scikit-learn",
        "algorithm": "RandomForestClassifier",
        "n_estimators": int(estimators),
        "random_state": 42,
        "sha256": model_sha256,
    },
}
os.makedirs(os.path.dirname(executor_output_path), exist_ok=True)
with open(executor_output_path, "w", encoding="utf-8") as stream:
    json.dump({"artifacts": {"model_out": {"artifacts": [runtime_artifact]}}}, stream)
print(f"model={output} sha256={model_sha256}")
'''

# Evaluate the model and publish scalar metrics as a Metrics artifact.
EVALUATE = r'''
import json, os, sys, joblib, pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
test_path, model_path, metrics_path, executor_input_json = sys.argv[1:5]
features = ["amount", "age", "tenure_months", "num_claims",
            "credit_score", "distance_km", "channel"]
frame = pd.read_csv(test_path)
model = joblib.load(model_path)
prediction = model.predict(frame[features])
probability = model.predict_proba(frame[features])[:, 1]
accuracy = float(accuracy_score(frame["label"], prediction))
roc_auc = float(roc_auc_score(frame["label"], probability))

# Keep a readable artifact file for preview or download from object storage.
os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
with open(metrics_path, "w", encoding="utf-8") as stream:
    json.dump({"accuracy": accuracy, "roc_auc": roc_auc}, stream)

# KFP v2 renders scalar metrics from Artifact metadata, not file contents.
# The {{$}} placeholder supplies the runtime Artifact URI and output metadata path.
executor_input = json.loads(executor_input_json)
executor_output_path = executor_input["outputs"]["outputFile"]
metrics_artifact = executor_input["outputs"]["artifacts"]["metrics"]["artifacts"][0]
runtime_artifact = {
    "name": metrics_artifact["name"],
    "uri": metrics_artifact["uri"],
    "metadata": {"accuracy": accuracy, "roc_auc": roc_auc},
}
os.makedirs(os.path.dirname(executor_output_path), exist_ok=True)
with open(executor_output_path, "w", encoding="utf-8") as stream:
    json.dump({"artifacts": {"metrics": {"artifacts": [runtime_artifact]}}}, stream)
print(f"accuracy={accuracy:.3f} roc_auc={roc_auc:.3f}")
'''

# Container Components avoid runtime pip installs in the disconnected cluster.
@dsl.container_component
def preprocess(source: dsl.Input[dsl.Dataset],
               train_out: dsl.Output[dsl.Dataset],
               test_out: dsl.Output[dsl.Dataset]):
    return dsl.ContainerSpec(
        image=IMAGE, command=["python", "-c"],
        args=[PREPROCESS, source.path, train_out.path, test_out.path])

@dsl.container_component
def train(train_in: dsl.Input[dsl.Dataset], n_estimators: int,
          model_out: dsl.Output[dsl.Model]):
    return dsl.ContainerSpec(
        image=IMAGE, command=["python", "-c"],
        args=[
            TRAIN,
            train_in.path,
            n_estimators,
            model_out.path,
            dsl.PIPELINE_TASK_EXECUTOR_INPUT_PLACEHOLDER])

@dsl.container_component
def evaluate(test_in: dsl.Input[dsl.Dataset],
             model_in: dsl.Input[dsl.Model],
             metrics: dsl.Output[dsl.Metrics]):
    return dsl.ContainerSpec(
        image=IMAGE, command=["python", "-c"],
        args=[
            EVALUATE,
            test_in.path,
            model_in.path,
            metrics.path,
            dsl.PIPELINE_TASK_EXECUTOR_INPUT_PLACEHOLDER])

@dsl.pipeline(name="fraud-training-pipeline")
def fraud_pipeline(
    dataset_uri: str = "s3://rhoai-pipelines/input/fraud_sample.csv",
    n_estimators: int = 100,
):
    # Reimport checks the source URI and creates a fresh input artifact per Run.
    source = dsl.importer(
        artifact_uri=dataset_uri, artifact_class=dsl.Dataset, reimport=True)
    # Artifact dependencies enforce preprocess -> train -> evaluate ordering.
    prepared = preprocess(source=source.output)
    trained = train(
        train_in=prepared.outputs["train_out"],
        n_estimators=n_estimators)
    evaluate(
        test_in=prepared.outputs["test_out"],
        model_in=trained.outputs["model_out"])

if __name__ == "__main__":
    # Compile the Python DSL into the portable KFP v2 Pipeline specification.
    compiler.Compiler().compile(
        pipeline_func=fraud_pipeline,
        package_path="/tmp/day07-fraud-pipeline.yaml")
PY

oc cp /tmp/python3/day07-pipeline.py \
  jukebox/day07-compiler:/tmp/day07-pipeline.py
oc exec -n jukebox day07-compiler -- \
  python /tmp/day07-pipeline.py
oc cp jukebox/day07-compiler:/tmp/day07-fraud-pipeline.yaml \
  /tmp/python3/day07-fraud-pipeline.yaml
```

### Pipeline 업로드
1. RHOAI 대시보드에서 `jukebox` 프로젝트를 선택한다.
2. Pipelines에서 `/tmp/python3/day07-fraud-pipeline.yaml`을 업로드한다.

동일한 `fraud-training-pipeline`이 이미 있으면 새 Pipeline을 만들지 않는다. 기존 Pipeline 상세 화면에서 `Actions` -> `Upload new version`을 선택하고 새로 컴파일한 YAML을 버전 이름 `lineage-metadata-v3`로 업로드한다. 이후 Run 생성 시 이 Pipeline version을 선택한다.

### CLI로 Pipeline 업로드
UI 대신 KFP SDK로 Pipeline을 업로드할 수 있다. DSPA가 생성한 NetworkPolicy는 Workbench의 API 접근을 허용하지만 일반 임시 Pod는 허용하지 않으므로, `day07-compiler`가 아니라 `jukebox-workbench-0`에서 KFP Client를 실행한다.

```bash
# 컴파일된 Pipeline YAML을 Workbench로 복사한다.
oc cp /tmp/python3/day07-fraud-pipeline.yaml \
  jukebox/jukebox-workbench-0:/tmp/day07-fraud-pipeline.yaml \
  -c jukebox-workbench

# OpenShift service CA로 내부 DSPA HTTPS API 인증서를 검증하며 업로드한다.
oc exec -i -n jukebox jukebox-workbench-0 \
  -c jukebox-workbench -- python - <<'PY'
from kfp import Client

client = Client(
    host="https://ds-pipeline-dspa.jukebox.svc:8888",
    namespace="jukebox",
    ssl_ca_cert=(
        "/var/run/secrets/kubernetes.io/"
        "serviceaccount/service-ca.crt"
    ),
    verify_ssl=True,
)

pipelines = client.list_pipelines(page_size=100, namespace="jukebox")
existing = next(
    (item for item in (pipelines.pipelines or [])
     if item.display_name == "fraud-training-pipeline"),
    None,
)

if existing:
    pipeline = client.upload_pipeline_version(
        pipeline_package_path="/tmp/day07-fraud-pipeline.yaml",
        pipeline_version_name="lineage-metadata-v3",
        pipeline_id=existing.pipeline_id,
        description="Day 7 scalar metrics metadata",
    )
else:
    pipeline = client.upload_pipeline(
        pipeline_package_path="/tmp/day07-fraud-pipeline.yaml",
        pipeline_name="fraud-training-pipeline",
        description="Day 7 fraud training pipeline",
        namespace="jukebox",
    )

print(pipeline)
PY
```

업로드 목록을 CLI에서 확인한다.

```bash
oc exec -i -n jukebox jukebox-workbench-0 \
  -c jukebox-workbench -- python - <<'PY'
from kfp import Client

client = Client(
    host="https://ds-pipeline-dspa.jukebox.svc:8888",
    namespace="jukebox",
    ssl_ca_cert=(
        "/var/run/secrets/kubernetes.io/"
        "serviceaccount/service-ca.crt"
    ),
    verify_ssl=True,
)

print(client.list_pipelines())
PY
```

### Pipeline Run 실행
Pipeline을 UI 또는 CLI로 업로드한 뒤 RHOAI 대시보드에서 Run을 생성한다.

1. 왼쪽 메뉴에서 `Develop & train` -> `Pipelines` -> `Pipeline definitions`로 이동한다.
2. 프로젝트로 `jukebox`를 선택한다.
3. `fraud-training-pipeline`을 선택한다.
4. Pipeline 상세 화면에서 `Actions` -> `Create run`을 선택한다.
5. 다음 값으로 기본 Run을 생성한다.

| 항목               | 값                                             |
| ---------------- | --------------------------------------------- |
| Run group        | `Default`                                     |
| Name             | `fraud-n100`                                  |
| Pipeline         | `fraud-training-pipeline`                     |
| Pipeline version | 현재 업로드한 버전                                    |
| `dataset_uri`    | `s3://rhoai-pipelines/input/fraud_sample.csv` |
| `n_estimators`   | `100`                                         |

`Run group`은 관련 Pipeline Run을 묶어서 비교하는 단위다. 기본 실습에서는 `Default`를 사용한다.

6. 같은 `Default` Run group에서 `n_estimators`만 변경한 Run을 두 개 더 생성한다. 나머지 parameter는 동일하게 유지한다.

| Run group | Name         | `n_estimators` |
| --------- | ------------ | -------------: |
| `Default` | `fraud-n20`  |           `20` |
| `Default` | `fraud-n100` |          `100` |
| `Default` | `fraud-n200` |          `200` |

이전 Pipeline version의 Run이 이미 있으면 새 version 검증 Run은 `fraud-v3-n20`, `fraud-v3-n100`, `fraud-v3-n200`처럼 구분해서 생성한다. 기존 Run의 Artifact metadata는 Pipeline version을 올려도 소급 변경되지 않는다.

각 Run이 완료되면 다음 순서로 metric과 실행 시간을 확인한다.

1. 왼쪽 메뉴에서 `Develop & train` -> `Pipelines` -> `Runs`로 이동한다.
2. 프로젝트로 `jukebox`를 선택하고 `Active runs` 탭을 연다.
3. `Run group` 열 또는 필터에서 `Default`에 속한 Run을 확인한다.
4. 비교할 `fraud-n20`, `fraud-n100`, `fraud-n200`의 체크박스를 선택한다. 새 version을 재검증하는 경우에는 이름을 구분한 `fraud-v3-n20`, `fraud-v3-n100`, `fraud-v3-n200`을 선택한다.
5. 목록 상단의 `Compare runs`를 클릭한다.
6. 비교 화면에서 scalar metric인 `accuracy`, `roc_auc`와 Run별 실행 시간을 비교한다.
7. 개별 Run 이름을 열어 그래프의 `evaluate` 단계를 선택하면 `Output artifacts`의 `metrics` metadata에서도 같은 값을 확인할 수 있다.

현재 Pipeline은 원본 S3 객체를 매번 다시 확인하도록 importer에 `reimport=True`를 사용하므로, Run마다 새로운 입력 Artifact가 생성되어 `preprocess`도 다시 실행될 수 있다. `n_estimators`가 달라진 `train`과 새 모델을 입력받는 `evaluate`는 반드시 다시 실행된다.

### 검증
```bash
oc get workflows.argoproj.io -n jukebox
oc get pods -n jukebox | grep fraud-training
mc ls --recursive truenas/rhoai-pipelines | tail -30
```

정상 실행 시 `preprocess -> train -> evaluate`가 모두 성공하고 Run 비교 화면과 `evaluate`의 `metrics` metadata에 `accuracy`, `roc_auc`가 표시된다. `train` 단계의 `model_out`에는 `algorithm`, `n_estimators`, `random_state`, `sha256` metadata도 표시되어야 한다. 값이 `-`이거나 model metadata가 없으면 이전 Pipeline version을 실행한 것이므로 `lineage-metadata-v3` 이후 version인지 확인한다. 검증 환경의 기본 실행 결과는 `train=4000`, `test=1000`, `accuracy=0.973`, `roc_auc=0.708`이었다.

### Day8에서 사용할 baseline과 candidate 확정
Day8은 Day5 모델을 다시 사용하지 않는다. 이 실습에서는 Day7의 성공한 KFP Run 중 `fraud-n20`을 v1 baseline, `fraud-n200`을 v2 candidate로 고정한다. 이는 모델 lineage와 배포 전환을 관찰하기 위한 선택이며, estimator 수가 많은 모델이 항상 더 우수하다는 의미는 아니다.

동일한 이름으로 Run을 여러 번 실행했다면 가장 최근에 성공한 Run을 선택한다. 새 Pipeline version 검증용으로 `fraud-v3-n20`, `fraud-v3-n200` 같은 이름을 사용했다면 아래 두 변수만 실제 Run 이름으로 바꾼다.

```bash
get_latest_run_id() {
  local run_name="$1"
  oc get workflows.argoproj.io -n jukebox -o json | jq -r \
    --arg name "$run_name" '
      [.items[]
       | select(.metadata.annotations["pipelines.kubeflow.org/run_name"] == $name)
       | select(.status.phase == "Succeeded")]
      | sort_by(.metadata.creationTimestamp)
      | last
      | .metadata.labels["pipeline/runid"]
    '
}

# 새 version용 이름을 사용했다면 실행 전에 이 값을 변경한다.
# 예: V1_RUN_NAME=fraud-v3-n20 V2_RUN_NAME=fraud-v3-n200
V1_RUN_NAME="${V1_RUN_NAME:-fraud-n20}"
V2_RUN_NAME="${V2_RUN_NAME:-fraud-n200}"
V1_RUN_ID="$(get_latest_run_id "$V1_RUN_NAME")"
V2_RUN_ID="$(get_latest_run_id "$V2_RUN_NAME")"

test -n "$V1_RUN_ID" && test "$V1_RUN_ID" != null
test -n "$V2_RUN_ID" && test "$V2_RUN_ID" != null

V1_KFP_ARTIFACT="$(
  mc find \
    "truenas/rhoai-pipelines/fraud-training-pipeline/${V1_RUN_ID}/train" \
    --name model_out | tail -1
)"
V2_KFP_ARTIFACT="$(
  mc find \
    "truenas/rhoai-pipelines/fraud-training-pipeline/${V2_RUN_ID}/train" \
    --name model_out | tail -1
)"

test -n "$V1_KFP_ARTIFACT"
test -n "$V2_KFP_ARTIFACT"

printf 'v1 run=%s id=%s artifact=%s\n' \
  "$V1_RUN_NAME" "$V1_RUN_ID" "$V1_KFP_ARTIFACT"
printf 'v2 run=%s id=%s artifact=%s\n' \
  "$V2_RUN_NAME" "$V2_RUN_ID" "$V2_KFP_ARTIFACT"

cat > /tmp/day7-lineage.env <<EOF
V1_RUN_NAME=${V1_RUN_NAME}
V1_RUN_ID=${V1_RUN_ID}
V1_KFP_ARTIFACT=${V1_KFP_ARTIFACT}
V2_RUN_NAME=${V2_RUN_NAME}
V2_RUN_ID=${V2_RUN_ID}
V2_KFP_ARTIFACT=${V2_KFP_ARTIFACT}
EOF
```

`V1_RUN_ID`와 `V2_RUN_ID`가 서로 다르고 두 `model_out` 객체가 존재해야 한다. `/tmp/day7-lineage.env`에는 인증정보가 없으며 Day8에서 같은 KFP artifact를 승격하는 데 사용한다.

### 실패 재현
`dataset_uri`를 `s3://rhoai-pipelines/input/not-found.csv`로 바꿔 실패 로그를 확인한 뒤 정상 URI로 새 Run을 생성한다. 이전 실패 Run을 수정하지 않는다.

### compiler Pod 정리
```bash
oc delete pod day07-compiler -n jukebox --ignore-not-found
```
