# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 4 Tekton CI와 Argo CD 연결

> 사전 활성화: [Week5 Step 3](<Week5-Step3 실습.md>)의 source/GitOps 저장소를 준비하고 두 저장소에 같은 Gitea PAT로 접근할 수 있어야 한다.

Argo CD가 비공개 GitOps 저장소를 읽도록 등록하고, Tekton Pipeline과 Gitea webhook을 구성한다. 첫 실행은 webhook보다 문제를 분리하기 쉬운 수동 PipelineRun으로 검증한다.

### Argo CD repository Secret

공개 문서나 Git 저장소에 실제 ID/PAT를 기록하지 않는다. 랩의 Gitea Route는 사설 인증서를 사용하므로 `insecure: "true"`로 시작하되, 운영에서는 Gitea CA를 Argo CD trust store에 추가한다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: week5-llm-gitops-repository
  namespace: openshift-gitops
  labels:
    argocd.argoproj.io/secret-type: repository
type: Opaque
stringData:
  type: git
  url: https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-gitops.git
  username: <GITEA_ID>
  password: <GITEA_PAT>
  insecure: "true"
EOF
```

### Argo CD Application 생성

```bash
oc apply -f \
  /tmp/python3/manifests/week5-llm-mlops-gitops.yaml

oc get applications.argoproj.io -n openshift-gitops \
  | grep week5-llm
```

초기에는 세 Application 모두 `Synced`여야 한다. serving Application의 초기 Git에는 ServingRuntime만 있고 InferenceService는 아직 없다.

### Tekton Pipeline과 Trigger 생성

```bash
oc apply -f \
  /tmp/python3/manifests/week5-llm-mlops-tekton.yaml

oc get pipeline -n rhoai-llm-mlops
oc get eventlistener,triggerbinding,triggertemplate \
  -n rhoai-llm-mlops
oc get route week5-gitea-webhook -n rhoai-llm-mlops
```

`week5-llm-ci`는 다음 순서로 동작한다.

1. source clone과 Python/dataset 검증
2. Buildah로 training image build 후 모델 registry `5010`에 push
3. image digest를 넣은 Kubernetes-native KFP Pipeline/PipelineVersion compile
4. compile 결과를 GitOps 저장소의 `pipelines/`에 push
5. Argo CD 동기화를 기다린 뒤 KFP Run 생성

`week5-llm-promote`는 Model Registry의 `stage`와 `train_loss` gate를 통과한 모델만 환경별 Git 선언에 반영한다.

### 첫 CI 수동 실행

같은 source commit으로 재실행하면 TrainJob 이름과 Model Version이 충돌하므로, 코드에 작은 변경을 commit한 뒤 실행하거나 새 commit을 push한다.

```bash
cat > /tmp/week5-ci-pipelinerun.yaml <<'EOF'
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: week5-llm-ci-manual-
  namespace: rhoai-llm-mlops
spec:
  pipelineRef:
    name: week5-llm-ci
  taskRunTemplate:
    serviceAccountName: llm-ci
  taskRunSpecs:
    - pipelineTaskName: build-runtime
      serviceAccountName: llm-build
  params:
    - name: source-revision
      value: main
  workspaces:
    - name: shared
      volumeClaimTemplate:
        spec:
          storageClassName: truenas-nfs
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 5Gi
    - name: git-credentials
      secret:
        secretName: gitea-credentials
EOF

PR_NAME=$(oc create -f /tmp/week5-ci-pipelinerun.yaml \
  -o jsonpath='{.metadata.name}')
echo "$PR_NAME"

tkn pipelinerun logs -n rhoai-llm-mlops \
  "$PR_NAME" -f
```

`tkn`이 없으면 다음 명령으로 상태와 task log를 확인한다.

```bash
oc get pipelinerun "$PR_NAME" -n rhoai-llm-mlops -w
oc logs -n rhoai-llm-mlops \
  -l tekton.dev/pipelineRun="$PR_NAME" --all-containers --prefix
```

### Gitea webhook 연결

```bash
WEBHOOK_URL="https://$(oc get route week5-gitea-webhook \
  -n rhoai-llm-mlops -o jsonpath='{.spec.host}')"
echo "$WEBHOOK_URL"
```

Gitea의 `week5-llm-source` 저장소에서 `Settings` -> `Webhooks` -> `Add Webhook` -> `Gitea`를 선택한다.

- Target URL: 위 `WEBHOOK_URL`
- HTTP Method: `POST`
- POST Content Type: `application/json`
- Trigger On: Push Events
- Active: 활성화

저장 후 Test Delivery의 HTTP status가 2xx인지 확인한다. 이 랩의 generic EventListener는 `X-Gitea-Event`와 `main` branch만 검사하고 webhook secret 서명을 검증하지 않는다. VPN 내부 학습환경에서만 사용하고, 운영에서는 지원되는 SCM interceptor 또는 서명을 검증하는 proxy/API gateway를 앞에 둔다.

### 확인 기준

- Argo CD Application 세 개가 `Synced`다.
- Tekton Pipeline 두 개와 EventListener Route가 존재한다.
- 수동 PipelineRun이 시작되고 `clone-and-validate` task가 성공한다.
- Gitea Test Delivery가 EventListener에 도달한다.
- Secret 실제 값은 문서와 저장소에 남지 않는다.
