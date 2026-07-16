# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 4 Tekton CI와 Argo CD 연결

> 사전 활성화: [Week5 Step 3](<Week5-Step3 실습.md>)의 source/GitOps 저장소를 준비하고 두 저장소에 같은 Gitea PAT로 접근할 수 있어야 한다.

Argo CD가 비공개 GitOps 저장소를 읽도록 등록하고, Tekton Pipeline과 Gitea webhook을 구성한다. 첫 실행은 webhook보다 문제를 분리하기 쉬운 수동 PipelineRun으로 검증한다.

### Argo CD repository Secret

공개 문서나 Git 저장소에 실제 ID/PAT를 기록하지 않는다. 검증 환경의 Gitea Route는 사설 인증서를 사용하므로 `insecure: "true"`로 시작하되, 운영에서는 Gitea CA를 Argo CD trust store에 추가한다.

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
oc apply -f - <<'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: week5-llm-pipelines
  namespace: openshift-gitops
spec:
  project: default
  source:
    repoURL: https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-gitops.git
    targetRevision: main
    path: pipelines
  destination:
    server: https://kubernetes.default.svc
    namespace: rhoai-llm-mlops
  syncPolicy:
    automated:
      prune: false
      selfHeal: true
    syncOptions: [CreateNamespace=false]
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: week5-llm-serving-production
  namespace: openshift-gitops
spec:
  project: default
  source:
    repoURL: https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-gitops.git
    targetRevision: main
    path: environments/production
  destination:
    server: https://kubernetes.default.svc
    namespace: rhoai-llm-production
  syncPolicy:
    automated:
      prune: false
      selfHeal: true
    syncOptions: [CreateNamespace=false]
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: week5-llm-serving-staging
  namespace: openshift-gitops
spec:
  project: default
  source:
    repoURL: https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-gitops.git
    targetRevision: main
    path: environments/staging
  destination:
    server: https://kubernetes.default.svc
    namespace: rhoai-llm-staging
  syncPolicy:
    automated:
      prune: false
      selfHeal: true
    syncOptions: [CreateNamespace=false]
EOF

oc get applications.argoproj.io -n openshift-gitops \
  | grep week5-llm
```

초기에는 세 Application 모두 `Synced`여야 한다. serving Application의 초기 Git에는 ServingRuntime만 있고 InferenceService는 아직 없다.

### Tekton Pipeline과 Trigger 생성

[Week5 Step 4 Tekton 리소스 적용](<Week5-Step4-Tekton 리소스.md>)의 heredoc 블록을 실행한다. 외부 YAML 파일은 필요하지 않다.

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

`start-kfp-run`에서 `ds-pipeline-dspa.rhoai-llm-mlops.svc:8888` 연결 timeout이 발생하면 [Week5 Step 4 - Tekton 리소스](<Week5-Step4-Tekton 리소스.md>)의 `allow-week5-start-kfp-run` NetworkPolicy가 적용됐는지 확인한다.

```bash
oc get networkpolicy allow-week5-start-kfp-run \
  -n rhoai-llm-mlops
```

`Argo CD did not publish the KFP version in time`으로 실패하면 KFP API 연결이 아니라 `week5-llm-pipelines` Application의 동기화 결과를 확인한다.

```bash
oc get applications.argoproj.io week5-llm-pipelines \
  -n openshift-gitops
oc get applications.argoproj.io week5-llm-pipelines \
  -n openshift-gitops -o json | \
  jq -r '.status.operationState.syncResult.resources[]? |
    [.kind, .name, .status, .message] | @tsv'
```

`cannot set blockOwnerDeletion`과 `can't set finalizers`가 함께 나오면 [Week5 Step 4 - Tekton 리소스](<Week5-Step4-Tekton 리소스.md>)의 `week5-argocd-kfp-finalizers` Role·RoleBinding 적용 여부를 확인한다. 이 권한을 적용한 뒤 Application이 `Synced`가 되고 새 `PipelineVersion`이 생성돼야 한다.

```bash
oc get role,rolebinding week5-argocd-kfp-finalizers \
  -n rhoai-llm-mlops
oc get pipelineversions.pipelines.kubeflow.org \
  -n rhoai-llm-mlops
```

같은 source commit을 재실행했을 때 Argo CD가 `Pipeline spec is immutable`로 실패하면 commit tag의 image를 덮어쓴 실행이 있었는지 확인한다. [Week5 Step 4 - Tekton 리소스](<Week5-Step4-Tekton 리소스.md>)의 `build-runtime`은 이미 존재하는 commit tag의 digest를 재사용해야 하며, 새 image가 필요하면 source 변경을 새 commit으로 기록한 뒤 실행한다.

실패한 PipelineRun은 중간부터 재개되지 않는다. 정책을 적용한 뒤 source 저장소에 새 commit을 만들고 이 절의 PipelineRun을 새로 생성한다. 이미 webhook을 연결했다면 새 commit을 push하는 것만으로 다음 절의 자동 PipelineRun이 생성되므로 수동 실행과 중복 실행하지 않는다.

### Disconnected Git server 사전 설정

Webhook 송신 서버와 EventListener가 모두 내부망에 있는 disconnected 환경에서도 HTTPS Route를 기준 endpoint로 사용한다. 이를 통해 Git server가 같은 클러스터 안에 있거나 별도 관리망에 있어도 같은 구성을 사용할 수 있다.

공통 사전조건은 다음과 같다.

1. Git server에서 EventListener Route FQDN이 내부 IP로 정상 해석되고 TCP `443`에 연결돼야 한다.
2. Route 인증서를 서명한 사내 CA 또는 OpenShift Ingress CA를 Git server OS·컨테이너 trust store에 등록한다. SSL 검증 비활성화는 사용하지 않는다.
3. Webhook의 로컬 네트워크 접근 범위는 내부망 전체가 아니라 EventListener Route FQDN으로 제한한다.
4. Webhook 토큰은 수신 측 Secret과 송신 측 webhook 설정에만 저장한다.

Gitea는 기본 `webhook.ALLOWED_HOST_LIST=external` 설정 때문에 내부 IP로 해석되는 Route 전송을 차단한다. Gitea 관리자는 `app.ini` 또는 Helm values에 다음처럼 정확한 Route FQDN을 추가하고 Gitea를 재시작한다. `private`나 `*`로 내부망 전체를 허용하지 않는다.

```ini
[webhook]
ALLOWED_HOST_LIST = week5-gitea-webhook-rhoai-llm-mlops.apps.sno.ocp422.com
```

OpenShift 기본 Ingress 인증서를 사용하는 랩은 `openshift-config-managed/default-ingress-cert`의 `ca-bundle.crt`를 Gitea의 기존 시스템 CA bundle에 추가한다. 운영 클러스터는 사내 CA가 서명한 Ingress 인증서를 사용하고 해당 CA를 Git server의 표준 trust store로 배포하는 방식을 우선한다. Gitea 설정 항목은 [Gitea Configuration Cheat Sheet](https://docs.gitea.com/administration/config-cheat-sheet#webhook-webhook)를 참고한다.

Self-Managed GitLab을 사용하는 경우 관리자가 `Admin` -> `Settings` -> `Network` -> `Outbound requests`에서 로컬 네트워크 webhook을 허용하고 EventListener Route hostname을 allowlist에 추가한다. GitLab에도 같은 Route CA를 신뢰시킨다. GitLab payload와 header는 Gitea와 다르므로 이 문서의 Gitea TriggerBinding을 그대로 사용하지 않고 Tekton의 GitLab interceptor와 `X-Gitlab-Token` Secret 검증으로 바꾼다. 자세한 내용은 [GitLab outbound request filtering](https://docs.gitlab.com/security/webhooks/)과 [GitLab webhooks](https://docs.gitlab.com/user/project/integrations/webhooks/)를 참고한다.

### Gitea webhook 연결

```bash
WEBHOOK_URL="https://$(oc get route week5-gitea-webhook \
  -n rhoai-llm-mlops -o jsonpath='{.spec.host}')"
echo "$WEBHOOK_URL"
```

Gitea의 `week5-llm-source` 저장소에서 `Settings` -> `Webhooks` -> `Add Webhook` -> `Gitea`를 선택한다.

Kubernetes Secret에 저장된 값을 webhook의 Authorization Header에 입력한다. 출력값을 문서나 Git 저장소에 기록하지 않는다.

```bash
WEBHOOK_AUTH=$(oc get secret week5-gitea-webhook-token \
  -n rhoai-llm-mlops \
  -o jsonpath='{.data.authorization}' | base64 -d)
printf 'Authorization Header: %s\n' "$WEBHOOK_AUTH"
```

- Target URL: 위 `WEBHOOK_URL`
- HTTP Method: `POST`
- POST Content Type: `application/json`
- Authorization Header: 위에서 출력한 `Bearer ...` 전체 값
- Trigger On: Push Events
- Active: 활성화

저장 후 Test Delivery의 HTTP status가 2xx인지 확인하고 shell 변수는 제거한다.

```bash
unset WEBHOOK_AUTH
```

EventListener는 Authorization Header, `X-Gitea-Event=push`, `main` branch를 모두 통과한 요청만 처리한다. CEL `compareSecret()` 동작은 [Tekton CEL interceptor expressions](https://tekton.dev/docs/triggers/cel_expressions/#list-of-extension-functions)를 참고한다.

### 실제 push 이벤트로 PipelineRun 생성

수동 PipelineRun이 성공한 뒤 새 source commit을 push해 Gitea webhook부터 TriggerTemplate까지 전체 경로를 검증한다. 수동 실행과 webhook 실행이 동시에 GPU·build 자원을 사용하지 않도록 먼저 수동 실행 완료를 기다린다.

```bash
MANUAL_RUN=$(oc get pipelineruns.tekton.dev \
  -n rhoai-llm-mlops \
  -l tekton.dev/pipeline=week5-llm-ci \
  -o json | jq -r '
    [.items[]
     | select(.metadata.name | startswith("week5-llm-ci-manual-"))]
    | sort_by(.metadata.creationTimestamp)
    | last.metadata.name // empty')

test -n "$MANUAL_RUN"
oc wait pipelineruns.tekton.dev/"$MANUAL_RUN" \
  -n rhoai-llm-mlops \
  --for=condition=Succeeded=True --timeout=3600s

cd /tmp/week5-llm-source
printf 'webhook_verified_at=%s\n' "$(date -Iseconds)" \
  > WEBHOOK-TEST.txt
git add WEBHOOK-TEST.txt
git commit -m 'Verify Week 5 Gitea webhook trigger'
WEBHOOK_COMMIT=$(git rev-parse HEAD)
git push origin main
```

EventListener가 webhook을 처리할 때까지 기다린 뒤, 방금 push한 commit SHA를 `source-revision`으로 받은 PipelineRun을 찾는다.

```bash
WEBHOOK_RUN=""
for attempt in $(seq 1 30); do
  WEBHOOK_RUN=$(oc get pipelineruns.tekton.dev \
    -n rhoai-llm-mlops -o json | \
    jq -r --arg commit "$WEBHOOK_COMMIT" '
      .items[]
      | select(any(.spec.params[]?;
          .name == "source-revision" and .value == $commit))
      | .metadata.name' | head -1)

  [ -n "$WEBHOOK_RUN" ] && break
  sleep 2
done

test -n "$WEBHOOK_RUN"
echo "WEBHOOK_RUN=$WEBHOOK_RUN"

oc get pipelineruns.tekton.dev "$WEBHOOK_RUN" \
  -n rhoai-llm-mlops \
  -o custom-columns='NAME:.metadata.name,SOURCE_REVISION:.spec.params[?(@.name=="source-revision")].value,SUCCEEDED:.status.conditions[?(@.type=="Succeeded")].status,REASON:.status.conditions[?(@.type=="Succeeded")].reason'
```

출력의 `SOURCE_REVISION`이 `WEBHOOK_COMMIT`과 같아야 한다. 생성 직후 `SUCCEEDED=Unknown`, `REASON=Running`인 것은 정상이며, 이 webhook PipelineRun을 Step5에서 계속 추적한다.

### 확인 기준

- Argo CD Application 세 개가 `Synced`다.
- Tekton Pipeline 두 개와 EventListener Route가 존재한다.
- 수동 PipelineRun이 시작되고 `clone-and-validate` task가 성공한다.
- Gitea Test Delivery가 EventListener에 도달한다.
- 실제 main branch push로 새 PipelineRun이 생성되고 `source-revision`이 push한 commit SHA와 일치한다.
- Secret 실제 값은 문서와 저장소에 남지 않는다.
