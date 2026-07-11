# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day7

Data Science Pipeline을 이용해서 전처리 -> 훈련 -> 평가 단계를 재사용 가능한 파이프라인으로 실행한다.
폐쇄망 실습이므로 파이프라인 컴포넌트에서 외부 PyPI나 GitHub에 접근하지 않는다.

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
기존 모델 저장용 Secret과 분리해서 파이프라인 버킷과 인증정보를 관리한다.

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
RHOAI 3.4의 Pipeline Server는 `DataSciencePipelinesApplication` v1을 사용한다.
메타데이터 DB는 실습용 내장 MariaDB를 사용하고, 파이프라인 아티팩트는 외부 MinIO에 저장한다.

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
    # DSPA Operator는 jukebox의 S3 EgressIP 경로 밖에서 실행된다.
    # 이 홈랩에서는 health check를 생략하고 실제 Pipeline Run으로 S3를 검증한다.
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

oc get dspa dspa -n jukebox
oc get pods,pvc -n jukebox | grep -Ei 'ds-pipeline|mariadb|dspa'
```

`oc get dspa`의 `READY`가 `True`가 될 때까지 기다린다. 준비되지 않으면 먼저 DSPA 상태와 관련 Pod 이벤트를 확인한다.

> `disableHealthCheck: true`는 S3 검증을 생략한다는 뜻이지 S3를 사용하지 않는다는 뜻이 아니다. 실제 Pipeline Run의 importer와 artifact upload가 성공해야 최종 검증이 완료된다.

```bash
oc get dspa dspa -n jukebox -o yaml
oc get events -n jukebox --sort-by=.lastTimestamp | tail -30
```

### KFP 컴파일 환경 준비
컴파일에 필요한 KFP SDK wheel은 내부 Nexus PyPI hosted 저장소에 미리 반입되어 있어야 한다.
파이프라인 컴포넌트는 RHOAI가 제공하는 Datascience CPU runtime을 사용하므로 실행 중 `pip install`을 하지 않는다.

```bash
python3 -m venv /tmp/day07-kfp
source /tmp/day07-kfp/bin/activate

python3 -m pip --isolated install \
  --index-url http://192.168.10.50:8081/repository/pypi-hosted/simple \
  --trusted-host 192.168.10.50 \
  'kfp==2.14.6'

python3 -m pip check
python3 -c 'import kfp; print(kfp.__version__)'
```

### 3단계 파이프라인 작성
`dsl.importer`가 Pipeline Server의 S3 아티팩트 저장소에서 입력 CSV를 가져온다.

```bash
cat > /tmp/python3/day07-pipeline.py <<'PY'
from kfp import compiler, dsl


PIPELINE_IMAGE = (
    "registry.redhat.io/rhoai/"
    "odh-pipeline-runtime-datascience-cpu-py312-rhel9@"
    "sha256:ed6634540d78910ceedc826b871641fb3f66b27be45b50df31c504582204a661"
)


@dsl.component(base_image=PIPELINE_IMAGE)
def preprocess(
    source: dsl.Input[dsl.Dataset],
    train_out: dsl.Output[dsl.Dataset],
    test_out: dsl.Output[dsl.Dataset],
):
    import pandas as pd
    from sklearn.model_selection import train_test_split

    frame = pd.read_csv(source.path).dropna()
    train, test = train_test_split(frame, test_size=0.2, random_state=42)
    train.to_csv(train_out.path, index=False)
    test.to_csv(test_out.path, index=False)
    print(f"train={len(train)} test={len(test)}")


@dsl.component(base_image=PIPELINE_IMAGE)
def train(
    train_in: dsl.Input[dsl.Dataset],
    n_estimators: int,
    model_out: dsl.Output[dsl.Model],
):
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier

    features = [
        "amount", "age", "tenure_months", "num_claims",
        "credit_score", "distance_km", "channel",
    ]
    frame = pd.read_csv(train_in.path)
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=42,
    )
    model.fit(frame[features], frame["label"])
    joblib.dump(model, model_out.path)


@dsl.component(base_image=PIPELINE_IMAGE)
def evaluate(
    test_in: dsl.Input[dsl.Dataset],
    model_in: dsl.Input[dsl.Model],
    metrics: dsl.Output[dsl.Metrics],
):
    import joblib
    import pandas as pd
    from sklearn.metrics import accuracy_score, roc_auc_score

    features = [
        "amount", "age", "tenure_months", "num_claims",
        "credit_score", "distance_km", "channel",
    ]
    frame = pd.read_csv(test_in.path)
    model = joblib.load(model_in.path)
    prediction = model.predict(frame[features])
    probability = model.predict_proba(frame[features])[:, 1]
    accuracy = float(accuracy_score(frame["label"], prediction))
    roc_auc = float(roc_auc_score(frame["label"], probability))
    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("roc_auc", roc_auc)
    print(f"accuracy={accuracy:.3f} roc_auc={roc_auc:.3f}")


@dsl.pipeline(name="fraud-training-pipeline")
def fraud_pipeline(
    dataset_uri: str = "s3://rhoai-pipelines/input/fraud_sample.csv",
    n_estimators: int = 100,
):
    source = dsl.importer(
        artifact_uri=dataset_uri,
        artifact_class=dsl.Dataset,
        reimport=True,
    )
    prepared = preprocess(source=source.output)
    trained = train(
        train_in=prepared.outputs["train_out"],
        n_estimators=n_estimators,
    )
    evaluate(
        test_in=prepared.outputs["test_out"],
        model_in=trained.outputs["model_out"],
    )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=fraud_pipeline,
        package_path="/tmp/python3/day07-fraud-pipeline.yaml",
    )
    print("compiled -> /tmp/python3/day07-fraud-pipeline.yaml")
PY

source /tmp/day07-kfp/bin/activate
python3 /tmp/python3/day07-pipeline.py
ls -lh /tmp/python3/day07-fraud-pipeline.yaml
```

### Pipeline Run 실행
1. RHOAI 대시보드에서 `jukebox` 프로젝트를 선택한다.
2. Pipelines 메뉴에서 `/tmp/python3/day07-fraud-pipeline.yaml`을 업로드한다.
3. Experiment와 Run을 생성하고 기본 파라미터로 실행한다.
4. 동일 파이프라인을 `n_estimators=20`, `n_estimators=200`으로 다시 실행한다.
5. 각 Run의 `accuracy`, `roc_auc`, 실행시간을 비교한다.

### 검증
```bash
oc get pods -n jukebox | grep -Ei 'fraud-training|pipeline'
oc get workflows.argoproj.io -n jukebox
oc get events -n jukebox --sort-by=.lastTimestamp | tail -30
```

정상 실행 시 `preprocess`, `train`, `evaluate`가 순서대로 성공하고 평가 단계에 `accuracy`와 `roc_auc`가 기록된다.

실패한 경우 Pipeline Run 화면의 실패 task 로그와 다음 항목을 확인한다.

```bash
# 입력 파일 확인
mc stat truenas/rhoai-pipelines/input/fraud_sample.csv

# Pipeline Server와 workflow controller 확인
oc get dspa dspa -n jukebox -o yaml
oc get pods -n jukebox | grep -Ei 'pipeline|workflow|mariadb'

# ImagePullBackOff이면 실제 미러 매핑과 Pod가 요청한 이미지를 확인
oc get pod -n jukebox -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.image}{" "}{end}{"\n"}{end}'
```

### 실패 재현
`dataset_uri`를 존재하지 않는 S3 경로로 바꿔 한 번 실행한 뒤 실패 로그를 확인한다. 이후 정상 경로로 복원해 재실행한다.
