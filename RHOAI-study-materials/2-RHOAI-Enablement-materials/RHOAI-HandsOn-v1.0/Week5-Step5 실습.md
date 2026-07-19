# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 5 - Step 5 CI 결과와 Kubernetes-native KFP 검증

> 사전 활성화: [Week5 Step 4](<Week5-Step4 실습.md>)의 `week5-llm-ci` PipelineRun을 실행한다.

Tekton이 만든 training image digest, GitOps commit, Argo CD 동기화, KFP PipelineVersion과 Run이 하나의 source commit으로 연결되는지 확인한다.

### PipelineRun task 상태

```bash
PR_NAME=$(oc get pipelinerun -n rhoai-llm-mlops \
  -l tekton.dev/pipeline=week5-llm-ci \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[-1:].metadata.name}')

oc get pipelinerun "$PR_NAME" -n rhoai-llm-mlops \
  -o json | jq '{name:.metadata.name,
    succeeded:(.status.conditions[] | select(.type=="Succeeded")),
    tasks:[.status.childReferences[]? | {name:.name,task:.pipelineTaskName}]}'
```

최종 `Succeeded=True`가 아직 아니어도 `build-runtime`, `compile-native-pipeline`, `push-gitops`, `start-kfp-run` 순서로 진행되는지 확인한다.

### source commit과 image digest

```bash
oc get taskrun -n rhoai-llm-mlops \
  -l tekton.dev/pipelineRun="$PR_NAME" -o json | \
  jq -r '.items[] | .metadata.name as $name |
    (.status.results // [])[]? |
    [$name,.name,.value] | @tsv'
```

`clone-and-validate`의 `commit`, `build-runtime`의 `image-url`과 `image-digest`를 기록한다. digest는 `sha256:`으로 시작해야 하며 KFP compile에는 `image-url@image-digest`가 사용된다.

```bash
oc image info --insecure -o json \
  192.168.10.50:5010/rhoai-training/llm-lora-runtime:<SHORT_COMMIT> | \
  jq '{name:.name,digest:.digest}'
```

`<SHORT_COMMIT>`은 source commit 앞 12자리로 바꾼다.

### GitOps와 Argo CD 확인

```bash
cd /tmp/week5-llm-gitops
git pull --ff-only
find pipelines -maxdepth 1 -type f -print
git log -1 --oneline

oc get applications.argoproj.io week5-llm-pipelines -n openshift-gitops \
  -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status,REVISION:.status.sync.revision
```

`pipelines/support-assistant-<SHORT_COMMIT>.yaml`과 `pipelines/kustomization.yaml`이 있어야 한다. Git commit 후 Argo CD가 이를 `rhoai-llm-mlops` Namespace에 동기화한다.

### Pipeline과 PipelineVersion CR 확인

```bash
oc get pipelines.pipelines.kubeflow.org -n rhoai-llm-mlops
oc get pipelineversions.pipelines.kubeflow.org -n rhoai-llm-mlops

oc get pipelineversion -n rhoai-llm-mlops \
  -o json | jq -r '.items[] |
    [.metadata.name,.spec.pipelineName,.spec.displayName] | @tsv'
```

이 리소스는 Tekton `Pipeline`과 API group이 다르다.

| 리소스 | API group | 역할 |
|---|---|---|
| Tekton Pipeline | `tekton.dev` | CI task 순서와 실행 환경 |
| KFP Pipeline/PipelineVersion | `pipelines.kubeflow.org` | ML workflow 정의와 버전 |
| KFP Run | DSPA API/DB | 한 번의 ML workflow 실행 |

### KFP Run 생성 확인

RHOAI 대시보드에서 `rhoai-llm-mlops` 프로젝트를 선택하고 `Data Science Pipelines` -> `Runs`에서 `support-assistant-<SHORT_COMMIT>` Run을 연다.

CLI에서는 DSPA API를 port-forward한 뒤 확인한다.

```bash
oc port-forward -n rhoai-llm-mlops \
  svc/ds-pipeline-dspa 18888:8888
```

다른 Bastion 터미널에서 실행한다.

```bash
oc get configmap openshift-service-ca.crt -n rhoai-llm-mlops \
  -o jsonpath='{.data.service-ca\.crt}' \
  > /tmp/week5-service-ca.crt

curl --cacert /tmp/week5-service-ca.crt \
  --resolve ds-pipeline-dspa.rhoai-llm-mlops.svc:18888:127.0.0.1 \
  https://ds-pipeline-dspa.rhoai-llm-mlops.svc:18888/apis/v2beta1/runs | \
  jq .
```

`--resolve`는 port-forward 접속 주소를 service 인증서의 DNS 이름과 일치시킨다.

### 확인 기준

- source commit, image tag/digest, KFP version과 Run name을 상호 추적할 수 있다.
- GitOps 저장소에 compile된 KFP CR만 있고 registry 인증정보는 없다.
- Argo CD Application이 Git revision을 동기화했다.
- KFP Run이 생성되어 `train-model` 단계가 시작된다.
