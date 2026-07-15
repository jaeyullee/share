# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 6 TrainJob, 지표와 Model Registry 검증

> 사전 활성화: [Week5 Step 5](<Week5-Step5 실습.md>)에서 KFP Run의 `train-model` 단계가 시작된 것을 확인한다.

KFP component가 Kubeflow Trainer v2 TrainJob을 생성하고 기다리는 구조를 관찰한다. 학습 Pod가 직접 KFP component 안에서 실행되는 것이 아니라 Trainer controller가 JobSet과 GPU Pod를 관리한다.

### TrainJob과 GPU Pod 추적

```bash
oc get trainjob -n rhoai-llm-mlops -w
```

다른 Bastion 터미널에서 실행한다.

```bash
oc get jobset,pod -n rhoai-llm-mlops \
  -l app.kubernetes.io/part-of=week5-llm-mlops -o wide

oc get pod -n rhoai-llm-mlops \
  -l app.kubernetes.io/part-of=week5-llm-mlops \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.nodeName}{"\t"}{.spec.containers[0].resources.requests.nvidia\.com/gpu}{"\n"}{end}'
```

Pod는 `ocp-w01-gpu`에 배치되고 `nvidia.com/gpu=1`을 요청해야 한다. 학습 log를 확인한다.

```bash
TRAIN_POD=$(oc get pod -n rhoai-llm-mlops \
  -l app.kubernetes.io/part-of=week5-llm-mlops \
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

oc get pod -n rhoai-llm-mlops \
  -l app.kubernetes.io/part-of=week5-llm-mlops
```

`Complete` 또는 `Succeeded` condition이 True가 되면 KFP component가 S3의 `metrics.json`을 읽고 다음 `register-model` 단계로 진행한다. 학습 Pod가 `Completed`이면 GPU request는 더 이상 scheduler의 가용량을 점유하지 않는다.

### S3 산출물과 지표 확인

```bash
RUN_ID=<SHORT_COMMIT>

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
2. task의 Output artifacts에서 metrics artifact를 연다.
3. metadata의 `train_loss`, `train_runtime`, `samples`를 S3 `metrics.json`과 비교한다.
4. `register-model` task가 성공했는지 확인한다.

KFP Run 전체가 성공해야 다음 승격 단계로 진행한다.

### Model Registry 확인

RHOAI 대시보드에서 `AI hub` -> `Models` -> `Registry`로 이동해 기존 registry를 연다.

1. Registered Model `support-assistant`를 연다.
2. 이름이 `<SHORT_COMMIT>`인 Model Version을 연다.
3. 모델 위치가 `s3://rhoai-llm-mlops/models/support-assistant/<SHORT_COMMIT>/model`인지 확인한다.
4. custom properties의 `stage=Staging`, `git_commit`, `train_loss`, `train_runtime`을 확인한다.

Model Registry의 `state=LIVE`는 객체 생명주기이고 이 실습의 `stage=Staging/Production`은 배포 승인 단계를 나타내는 별도 custom property다.

### 확인 기준

- Trainer v2가 단일 GPU TrainJob을 완료했다.
- S3에 merged model, adapter와 metrics가 같은 Run ID 아래 존재한다.
- KFP metrics metadata와 S3 metrics가 일치한다.
- Model Registry 버전의 Git commit, S3 URI와 지표를 source commit까지 추적할 수 있다.
- staging 서빙 전 학습 Pod가 종료되어 GPU가 반환됐다.
