# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day7

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
이 랩에서는 DSPA Operator가 `jukebox`의 storage network EgressIP 경로 밖에서 실행되므로 Operator의 S3 health check만 생략한다. 실제 S3 연결은 Pipeline importer와 artifact upload로 검증한다.

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
    disableHealthCheck: true
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
`@dsl.component`는 실행 Pod에서 KFP package를 설치하려고 할 수 있다. 폐쇄망에서는 `@dsl.container_component`로 명령을 명시해서 runtime `pip install`을 제거한다.

```bash
cat > /tmp/python3/day07-pipeline.py <<'PY'
from kfp import compiler, dsl

IMAGE = (
    "registry.redhat.io/rhoai/"
    "odh-pipeline-runtime-datascience-cpu-py312-rhel9@"
    "sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661"
)

PREPROCESS = r'''
import os, sys, pandas as pd
from sklearn.model_selection import train_test_split
source, train_path, test_path = sys.argv[1:4]
frame = pd.read_csv(source).dropna()
train, test = train_test_split(frame, test_size=0.2, random_state=42)
for path in (train_path, test_path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
train.to_csv(train_path, index=False)
test.to_csv(test_path, index=False)
print(f"train={len(train)} test={len(test)}")
'''

TRAIN = r'''
import os, sys, joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier
source, estimators, output = sys.argv[1:4]
features = ["amount", "age", "tenure_months", "num_claims",
            "credit_score", "distance_km", "channel"]
frame = pd.read_csv(source)
model = RandomForestClassifier(n_estimators=int(estimators), random_state=42)
model.fit(frame[features], frame["label"])
os.makedirs(os.path.dirname(output), exist_ok=True)
joblib.dump(model, output)
print(f"model={output}")
'''

EVALUATE = r'''
import json, os, sys, joblib, pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
test_path, model_path, metrics_path = sys.argv[1:4]
features = ["amount", "age", "tenure_months", "num_claims",
            "credit_score", "distance_km", "channel"]
frame = pd.read_csv(test_path)
model = joblib.load(model_path)
prediction = model.predict(frame[features])
probability = model.predict_proba(frame[features])[:, 1]
accuracy = float(accuracy_score(frame["label"], prediction))
roc_auc = float(roc_auc_score(frame["label"], probability))
os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
with open(metrics_path, "w", encoding="utf-8") as stream:
    json.dump({"metrics": [
        {"name": "accuracy", "numberValue": accuracy, "format": "RAW"},
        {"name": "roc_auc", "numberValue": roc_auc, "format": "RAW"}
    ]}, stream)
print(f"accuracy={accuracy:.3f} roc_auc={roc_auc:.3f}")
'''

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
        args=[TRAIN, train_in.path, n_estimators, model_out.path])

@dsl.container_component
def evaluate(test_in: dsl.Input[dsl.Dataset],
             model_in: dsl.Input[dsl.Model],
             metrics: dsl.Output[dsl.Metrics]):
    return dsl.ContainerSpec(
        image=IMAGE, command=["python", "-c"],
        args=[EVALUATE, test_in.path, model_in.path, metrics.path])

@dsl.pipeline(name="fraud-training-pipeline")
def fraud_pipeline(
    dataset_uri: str = "s3://rhoai-pipelines/input/fraud_sample.csv",
    n_estimators: int = 100,
):
    source = dsl.importer(
        artifact_uri=dataset_uri, artifact_class=dsl.Dataset, reimport=True)
    prepared = preprocess(source=source.output)
    trained = train(
        train_in=prepared.outputs["train_out"],
        n_estimators=n_estimators)
    evaluate(
        test_in=prepared.outputs["test_out"],
        model_in=trained.outputs["model_out"])

if __name__ == "__main__":
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

### Pipeline Run 실행
1. RHOAI 대시보드에서 `jukebox` 프로젝트를 선택한다.
2. Pipelines에서 `/tmp/python3/day07-fraud-pipeline.yaml`을 업로드한다.
3. Experiment와 Run을 생성하고 기본 parameter로 실행한다.
4. `n_estimators=20`, `n_estimators=200`으로 다시 실행해 결과를 비교한다.

### 검증
```bash
oc get workflows.argoproj.io -n jukebox
oc get pods -n jukebox | grep fraud-training
mc ls --recursive truenas/rhoai-pipelines | tail -30
```

정상 실행 시 `preprocess -> train -> evaluate`가 모두 성공하고 Pipeline 화면에 `accuracy`, `roc_auc`가 표시된다. 검증 환경의 기본 실행 결과는 `train=4000`, `test=1000`, `accuracy=0.973`, `roc_auc=0.708`이었다.

### 실패 재현
`dataset_uri`를 `s3://rhoai-pipelines/input/not-found.csv`로 바꿔 실패 로그를 확인한 뒤 정상 URI로 새 Run을 생성한다. 이전 실패 Run을 수정하지 않는다.

### compiler Pod 정리
```bash
oc delete pod day07-compiler -n jukebox --ignore-not-found
```
