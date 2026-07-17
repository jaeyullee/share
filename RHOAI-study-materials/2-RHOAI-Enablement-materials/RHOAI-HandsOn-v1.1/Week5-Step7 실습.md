# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 7 Staging 승격과 vLLM 추론

> 사전 활성화: [Week5 Step 6](<Week5-Step6 실습.md>)의 KFP Run, S3 model과 Model Registry `stage=Staging` 검증을 완료하고 GPU가 비어 있어야 한다.

Tekton promotion gate가 Registry 상태와 학습 지표를 확인한 뒤 GitOps 저장소만 변경하도록 한다. Argo CD가 그 변경을 staging Namespace에 반영한다.

### 승격 입력 확인

```bash
RUN_ID=<SHORT_COMMIT>
MODEL_URI="s3://rhoai-llm-mlops/models/support-assistant/$RUN_ID/model"

mc cat \
  truenas/rhoai-llm-mlops/models/support-assistant/$RUN_ID/metrics.json | \
  jq '{run_id,git_commit,model_uri,train_loss,train_runtime}'
```

`RUN_ID`와 `MODEL_URI`는 Model Registry version과 같아야 한다. `max-train-loss=5.0`은 자동 gate 동작을 보기 위한 랩 기준일 뿐 모델 품질 기준이 아니다. 운영에서는 held-out 평가, 안전성, latency와 담당자 승인을 함께 사용한다.

### Staging promotion PipelineRun

```bash
cat > /tmp/week5-promote-staging.yaml <<EOF
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: week5-promote-staging-
  namespace: rhoai-llm-mlops
spec:
  pipelineRef:
    name: week5-llm-promote
  taskRunTemplate:
    serviceAccountName: llm-ci
  params:
    - name: version-name
      value: "$RUN_ID"
    - name: model-uri
      value: "$MODEL_URI"
    - name: max-train-loss
      value: "5.0"
    - name: environment
      value: staging
  workspaces:
    - name: shared
      volumeClaimTemplate:
        spec:
          storageClassName: truenas-nfs
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 1Gi
    - name: git-credentials
      secret:
        secretName: gitea-credentials
EOF

PROMOTE_RUN=$(oc create -f /tmp/week5-promote-staging.yaml \
  -o jsonpath='{.metadata.name}')

tkn pipelinerun logs -n rhoai-llm-mlops \
  "$PROMOTE_RUN" -f
```

`tkn`이 설치되지 않은 경우에는 다음 `oc` 경로를 사용한다. 첫 명령은 `Succeeded=True` 또는 `Succeeded=False`가 될 때까지 감시한다. 종료 후 TaskRun과 해당 Pod의 로그에서 `promotion gate passed`를 확인한다.

```bash
oc get pipelinerun "$PROMOTE_RUN" -n rhoai-llm-mlops -w

oc get taskrun -n rhoai-llm-mlops \
  -l tekton.dev/pipelineRun="$PROMOTE_RUN" -o wide

oc logs -n rhoai-llm-mlops \
  -l tekton.dev/pipelineRun="$PROMOTE_RUN" \
  --all-containers=true --prefix=true
```

`promotion gate passed`가 출력되고 GitOps 저장소의 staging `inferenceservice.json`과 `kustomization.yaml`이 commit된다.

### Argo CD와 KServe 상태

```bash
oc get applications.argoproj.io week5-llm-serving-staging \
  -n openshift-gitops -w
```

`Synced/Healthy`가 되면 `Ctrl+C`로 종료한다.

```bash
oc get servingruntime,isvc,pod -n rhoai-llm-staging -o wide
oc wait --for=condition=Ready \
  isvc/support-assistant-staging \
  -n rhoai-llm-staging --timeout=600s

oc get isvc support-assistant-staging -n rhoai-llm-staging \
  -o jsonpath='{.metadata.annotations.mlops\.opendatahub\.io/model-version}{"\n"}{.spec.predictor.model.storageUri}{"\n"}'
```

출력은 각각 `RUN_ID`와 `MODEL_URI`여야 한다.

### OpenAI 호환 chat completion 호출

첫 Bastion 터미널에서 실행한다.

```bash
oc port-forward -n rhoai-llm-staging \
  deploy/support-assistant-staging-predictor 18090:8080
```

다른 Bastion 터미널에서 실행한다.

```bash
cd /tmp/python3
export RHOAI_HANDSON_DIR="$PWD"
curl -sS -H 'Content-Type: application/json' \
  http://127.0.0.1:18090/v1/chat/completions \
  -d @"$RHOAI_HANDSON_DIR/models/llm-mlops/inference-request-staging.json" | \
  jq '{id,model,answer:.choices[0].message.content,usage}'
```

HTTP 200과 비어 있지 않은 `choices[0].message.content`가 반환돼야 한다. 응답 내용의 정확성은 24개 합성 sample로 보장할 수 없으며, 여기서는 serving contract와 배포 추적성을 검증한다.

### 잘못된 gate 재현

선택적으로 새 PipelineRun에서 `max-train-loss`를 실제 `train_loss`보다 작은 값으로 지정한다. PipelineRun이 실패하고 Git commit과 Argo CD 배포가 발생하지 않아야 한다.

```bash
oc get pipelinerun "$PROMOTE_RUN" -n rhoai-llm-mlops
cd /tmp/week5-llm-gitops && git pull --ff-only && git log -3 --oneline
```

### 확인 기준

- Registry `Staging`과 loss gate를 통과한 version만 Git에 반영됐다.
- Argo CD가 staging InferenceService를 생성했고 Ready다.
- ISVC annotation, storage URI와 Registry version이 일치한다.
- vLLM OpenAI 호환 API가 정상 응답한다.
- Tekton이 클러스터에 ISVC를 직접 `oc apply`하지 않았다.
