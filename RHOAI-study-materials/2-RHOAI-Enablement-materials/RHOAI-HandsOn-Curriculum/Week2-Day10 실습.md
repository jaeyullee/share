# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day10

> 사전 활성화: [Week1 Day1&2 - AI Pipelines와 Model Registry 구성](Week1-Day1%262-환경구성.md#ai-pipelines와-model-registry-구성), [KServe RawDeployment 구성](Week1-Day1%262-환경구성.md#kserve-rawdeployment-구성), GitOps 경로를 수행할 때는 [Argo CD GitOps 구성](Week1-Day1%262-환경구성.md#tekton-cicd와-argo-cd-gitops-구성)을 먼저 확인한다. Tekton은 이 Day의 필수 구성요소가 아니다.

Day6~9의 훈련, Registry, KServe, RBAC 흐름을 하나로 연결한다. 기본 E2E는 수동으로 수행하고, OpenShift GitOps가 설치된 환경에서는 InferenceService와 Route를 GitOps로 관리한다.

### 사전 상태 확인
```bash
oc get dspa -n jukebox
oc get modelregistries.modelregistry.opendatahub.io -n rhoai-model-registries
oc get servingruntime,isvc,route -n jukebox
mc stat truenas/rhoai-models/fraud/model.joblib
mc stat truenas/rhoai-models/fraud-v2/model.joblib
```

RHOAI 3.4의 현재 KServe는 이전 `RawDeployment` 계열을 `Standard` deployment mode로 표시한다. InferenceService가 `Standard`이고 Kubernetes Deployment와 Service를 직접 생성하면 이 실습의 KServe 선행 조건을 충족한다.

### E2E 수동 경로
1. Day7 KFP Pipeline Run으로 모델을 훈련하고 평가 지표를 확인한다.
2. Day8 Model Registry에 v1과 v2를 등록하고 v2를 `stage=Production`으로 승격한다.
3. Registry의 Production 버전 S3 URI로 `fraud-registry-production` InferenceService를 배포한다.
4. 추론 요청에 정상 응답하는지 확인한다.
5. Day5의 `fraud-route` weight를 이용해 기존 버전에서 새 버전으로 전환한다.

> 현재 기본 커리큘럼에서 Day7 KFP Run은 Pipeline 실행과 평가 gate를 확인하고, Day8은 Day5에서 만든 v1/v2 모델을 Registry에 등록한다. 따라서 Day7에서 생성된 모델 Artifact가 Day8 v2로 자동 전달되는 동일 모델 lineage는 아니다. 이 Day의 기본 E2E는 각 기능의 운영 연결을 수동으로 확인하는 범위이며, 동일 Artifact lineage 자동화는 별도 LLM MLOps 추가 스터디에서 다룬다.

### 1. Day7 KFP Run과 평가 gate 확인
RHOAI 대시보드에서 `jukebox` 프로젝트를 선택하고 `Develop & train` -> `Pipelines` -> `Runs`로 이동한다.

1. `Active runs`에서 `Default` Run group을 확인한다.
2. `fraud-n20`, `fraud-n100`, `fraud-n200`이 모두 성공했는지 확인한다.
3. 세 Run을 선택하고 `Compare runs`를 눌러 `accuracy`, `roc_auc`와 실행 시간을 비교한다.
4. 기준 Run인 `fraud-n100`을 열고 그래프의 `evaluate` task를 선택한다.
5. `Output artifacts`의 `metrics` metadata에 `accuracy`와 `roc_auc`가 숫자로 표시되는지 확인한다.

```bash
oc get workflows.argoproj.io -n jukebox \
  --sort-by=.metadata.creationTimestamp | tail -10

oc get pods -n jukebox | grep -E 'fraud|NAME'
oc get events -n jukebox --sort-by=.lastTimestamp | tail -20
```

검증 환경의 기본 `fraud-n100` 결과는 `accuracy=0.973`, `roc_auc=0.708`이었다. 정확한 값보다 Run 성공, scalar metrics 표시와 실패 Pod 부재를 확인하는 것이 이 단계의 기준이다. 값이 `-`이면 Day7의 이전 Pipeline version을 실행한 것이므로 `metrics-metadata-v2` 이후 version으로 Run을 다시 만든다.

### 2. Registry Production 버전 확인
Day8에서 `fraud-detection` Registered Model의 v1과 v2를 등록하고 다음 상태까지 완료했는지 확인한다.

- v2 모델 위치: `s3://rhoai-models/fraud-v2/model.joblib`
- v2 custom property: `stage=Production`
- v1 custom property: 필요에 따라 `stage=Archived`
- v2 Model Version ID가 기록되어 있음

`state=LIVE`는 Registry 객체의 생명주기이고 `stage=Production`은 이 커리큘럼의 배포 승인 custom property다.

### 3. Registry Production 버전으로 InferenceService 배포
첫 Bastion 터미널에서 Registry REST Service를 port-forward한다.

```bash
oc port-forward -n rhoai-model-registries \
  svc/jukebox-registry 18080:8080
```

다른 Bastion 터미널에서 Registry ID와 v2 Model Version ID를 다시 조회한다.

```bash
REGISTERED_MODEL_ID="$(
  curl -s http://127.0.0.1:18080/api/model_registry/v1alpha3/registered_models |
    jq -r '.items[] | select(.name == "fraud-detection") | .id'
)"

V2_MODEL_VERSION_ID="$(
  curl -s http://127.0.0.1:18080/api/model_registry/v1alpha3/model_versions |
    jq -r --arg id "$REGISTERED_MODEL_ID" \
      '.items[] | select(.registeredModelId == $id and .name == "v2") | .id'
)"

printf 'Registered Model ID=%s\nv2 Model Version ID=%s\n' \
  "$REGISTERED_MODEL_ID" "$V2_MODEL_VERSION_ID"

test -n "$REGISTERED_MODEL_ID"
test -n "$V2_MODEL_VERSION_ID"
mc stat truenas/rhoai-models/fraud-v2/model.joblib
```

두 ID가 비어 있지 않고 S3 object가 존재해야 한다. Day8을 앞에서 수행했다면 현재 환경의 예시는 Registered Model ID `1`, v2 Model Version ID `3`이지만 고정값으로 사용하지 않고 매번 조회한다.

Registry ID는 추적 annotation에 기록하고, 실제 모델 로딩 위치는 `storageUri`로 지정한다.

```bash
cat <<EOF | oc apply -f -
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-registry-production
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
    modelregistry.opendatahub.io/registered-model-id: "${REGISTERED_MODEL_ID}"
    modelregistry.opendatahub.io/model-version-id: "${V2_MODEL_VERSION_ID}"
spec:
  predictor:
    serviceAccountName: kserve-sa
    minReplicas: 1
    model:
      modelFormat:
        name: sklearn
        version: "1"
      runtime: mlserver-sklearn
      storageUri: s3://rhoai-models/fraud-v2
      env:
        - name: MLSERVER_MODEL_NAME
          value: fraud
      readinessProbe:
        httpGet:
          path: /v2/models/fraud/ready
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 5
        timeoutSeconds: 5
      livenessProbe:
        httpGet:
          path: /v2/models/fraud/ready
          port: 8080
        initialDelaySeconds: 20
        periodSeconds: 10
        timeoutSeconds: 5
EOF

oc wait --for=condition=Ready \
  isvc/fraud-registry-production -n jukebox --timeout=300s

oc get isvc fraud-registry-production -n jukebox \
  -o jsonpath='{.metadata.annotations.modelregistry\.opendatahub\.io/model-version-id}{"\n"}{.spec.predictor.model.storageUri}{"\n"}'
```

출력은 조회한 v2 Model Version ID와 `s3://rhoai-models/fraud-v2`여야 한다. 입력 annotation은 reconcile 후 `RawDeployment` 대신 `Standard`로 보일 수 있으며 Kubernetes Deployment와 Service가 생성되면 정상이다.

### 4. Production 모델 직접 추론 검증
먼저 predictor 상태와 모델 로딩 log를 확인한다.

```bash
oc get isvc fraud-registry-production -n jukebox
oc get deploy,pod -n jukebox \
  -l serving.kserve.io/inferenceservice=fraud-registry-production

oc logs -n jukebox \
  deploy/fraud-registry-production-predictor \
  -c kserve-container --tail=50
```

첫 Bastion 터미널에서 port-forward한다.

```bash
oc port-forward -n jukebox \
  deploy/fraud-registry-production-predictor 18088:8080
```

다른 Bastion 터미널에서 readiness와 추론을 호출한다.

```bash
curl -fsS http://127.0.0.1:18088/v2/models/fraud/ready

curl -sS -H 'Content-Type: application/json' \
  http://127.0.0.1:18088/v2/models/fraud/infer \
  -d @/tmp/python3/fraud-request.json | \
  tee /tmp/day10-production-response.json | jq .

jq -e '
  .model_name == "fraud" and
  .outputs[0].datatype == "INT64" and
  (.outputs[0].data | length) > 0
' /tmp/day10-production-response.json
```

마지막 `jq -e`가 종료 코드 `0`이면 응답 구조가 정상이다. Day5의 의도적인 v2 `DummyClassifier`를 그대로 사용했다면 `outputs[0].data[0]`은 `1`이다. `Ready=True`만 확인하지 말고 실제 inference protocol 응답까지 성공해야 이 단계를 통과한 것으로 본다.

### 5. Route weight로 기존 버전에서 Production 버전 전환
`fraud-blue-predictor`는 기존 v1, `fraud-registry-production-predictor`는 Registry에서 확인한 v2 Production 모델이다. 두 backend 모두 `MLSERVER_MODEL_NAME=fraud`를 사용하므로 같은 URL로 호출할 수 있다.

먼저 90:10으로 새 Production 모델에 일부 트래픽만 전달한다.

```bash
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"port":{"targetPort":"http"},"to":{"kind":"Service","name":"fraud-blue-predictor","weight":90},"alternateBackends":[{"kind":"Service","name":"fraud-registry-production-predictor","weight":10}]}}'

ROUTE="http://$(oc get route fraud-route -n jukebox \
  -o jsonpath='{.spec.host}')"

for i in $(seq 1 40); do
  curl -sS -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-request.json |
    jq -r '.outputs[0].data[0]'
done | sort | uniq -c
```

v1은 `0`, v2는 `1`을 반환하므로 대략 `0`이 36회, `1`이 4회에 가깝게 나온다. 요청 수가 적으므로 정확히 90:10일 필요는 없다.

50:50으로 확대해 다시 확인한다.

```bash
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":50},"alternateBackends":[{"kind":"Service","name":"fraud-registry-production-predictor","weight":50}]}}'

for i in $(seq 1 40); do
  curl -sS -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-request.json |
    jq -r '.outputs[0].data[0]'
done | sort | uniq -c
```

새 버전에 이상이 없으면 0:100으로 전환하고 새 모델 응답만 반환되는지 확인한다.

```bash
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":0},"alternateBackends":[{"kind":"Service","name":"fraud-registry-production-predictor","weight":100}]}}'

for i in $(seq 1 10); do
  curl -sS -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-request.json |
    jq -r '.outputs[0].data[0]'
done | sort | uniq -c
```

모두 `1`이면 전환이 완료된 것이다. 다음 GitOps 실습의 시작값을 일정하게 만들기 위해 90:10으로 복원한다.

```bash
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":90},"alternateBackends":[{"kind":"Service","name":"fraud-registry-production-predictor","weight":10}]}}'

oc get route fraud-route -n jukebox \
  -o jsonpath='{.spec.to.name}{"="}{.spec.to.weight}{" "}{range .spec.alternateBackends[*]}{.name}{"="}{.weight}{" "}{end}{"\n"}'
```

예상 최종 출력은 `fraud-blue-predictor=90 fraud-registry-production-predictor=10`이다. 실제 운영에서는 예측값만 보지 않고 오류율, latency와 업무 품질 지표를 관찰하면서 단계별로 확대하고 이상 시 즉시 100:0으로 되돌린다.

### GitOps Operator 확인
GitOps는 RHOAI `aipipelines`의 Argo Workflows와 다른 제품이다.

```bash
oc get subscription -A | grep openshift-gitops-operator
oc get pods -n openshift-gitops
oc get crd applications.argoproj.io
```

설치되어 있지 않으면 미러 CatalogSource의 `openshift-gitops-operator` 패키지를 별도로 설치한다.

기본 `openshift-gitops` Argo CD가 `jukebox` Namespace의 리소스를 관리하도록 label을 추가한다. 이 label은 Application Controller에 해당 Namespace의 admin 수준 권한을 부여하므로 운영환경에서는 별도 Argo CD 인스턴스와 축소된 공통 ClusterRole을 검토한다.

```bash
oc label namespace jukebox \
  argocd.argoproj.io/managed-by=openshift-gitops --overwrite

ARGO_SA=system:serviceaccount:openshift-gitops:openshift-gitops-argocd-application-controller

oc auth can-i create inferenceservices.serving.kserve.io \
  -n jukebox --as="$ARGO_SA"
oc auth can-i patch routes.route.openshift.io \
  -n jukebox --as="$ARGO_SA"
```

두 명령이 모두 `yes`여야 다음 Application이 InferenceService와 Route를 동기화할 수 있다.

### GitOps 저장소 준비
내부 Git 서버에 `rhoai-lab/day10-gitops` 저장소를 만들고 아래 구조로 배포 YAML을 저장한다.

```text
day10-gitops/
└── serving/
    ├── kustomization.yaml
    ├── inferenceservice.json
    └── route.json
```

```bash
mkdir -p /tmp/day10-gitops/serving
cd /tmp/day10-gitops/serving

cat > kustomization.yaml <<'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - inferenceservice.json
  - route.json
EOF

oc get isvc fraud-registry-production -n jukebox -o json | jq \
  'del(.metadata.creationTimestamp, .metadata.generation,
       .metadata.resourceVersion, .metadata.uid, .metadata.ownerReferences,
       .metadata.finalizers,
       .metadata.annotations["kubectl.kubernetes.io/last-applied-configuration"],
       .status)' > inferenceservice.json

oc get route fraud-route -n jukebox -o json | jq \
  'del(.metadata.creationTimestamp, .metadata.generation,
       .metadata.resourceVersion, .metadata.uid,
       .metadata.annotations["kubectl.kubernetes.io/last-applied-configuration"],
       .metadata.annotations["openshift.io/host.generated"],
       .status)' > route.json
```

YAML을 검토한 뒤 저장소에 push한다. 인증정보는 remote URL에 직접 넣지 않는다.

```bash
git init
git add .
git commit -m 'Add RHOAI serving resources'
git branch -M main
git remote add origin https://gitea.apps.sno.ocp422.com/rhoai-lab/day10-gitops.git
git push -u origin main
```

### 비공개 Git 저장소 인증 Secret
비공개 저장소는 이 Secret에 ID/PAT를 함께 넣는다. 저장소가 공개여도 Gitea Route가 사설 CA를 사용하고 Argo CD에 해당 CA를 배포하지 않았다면 `insecure: "true"`인 repository Secret은 필요하다. 운영 환경에서는 `insecure` 대신 Gitea CA를 Argo CD에 신뢰시키는 구성을 사용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: day10-gitops-repository
  namespace: openshift-gitops
  labels:
    argocd.argoproj.io/secret-type: repository
type: Opaque
stringData:
  type: git
  url: https://gitea.apps.sno.ocp422.com/rhoai-lab/day10-gitops.git
  username: <GITEA_ID>
  password: <GITEA_PAT>
  insecure: "true"
EOF
```

### Argo CD Application 생성
처음 검증할 때는 `prune`을 `false`로 두고, Git이 관리해야 할 리소스 범위를 확인한 뒤 활성화한다.

```bash
oc apply -f - <<'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: jukebox-serving
  namespace: openshift-gitops
spec:
  project: default
  source:
    repoURL: https://gitea.apps.sno.ocp422.com/rhoai-lab/day10-gitops.git
    targetRevision: main
    path: serving
  destination:
    server: https://kubernetes.default.svc
    namespace: jukebox
  syncPolicy:
    automated:
      prune: false
      selfHeal: true
    syncOptions:
      - CreateNamespace=false
EOF

oc get applications.argoproj.io jukebox-serving -n openshift-gitops
oc describe applications.argoproj.io jukebox-serving -n openshift-gitops
```

### GitOps 동작 검증
1. Route weight를 Git에서 `90:10`에서 `50:50`으로 변경하고 push한다.
2. Argo CD Application이 `Synced`와 `Healthy`가 되는지 확인한다.
3. 클러스터 Route에 변경된 weight가 반영됐는지 확인한다.

```bash
oc get applications.argoproj.io jukebox-serving -n openshift-gitops \
  -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status

oc get route fraud-route -n jukebox \
  -o jsonpath='{.spec.to.name}{"="}{.spec.to.weight}{" "}{range .spec.alternateBackends[*]}{.name}{"="}{.weight}{" "}{end}{"\n"}'
```

### Self-heal 검증
클러스터에서 Route weight를 직접 바꾼 뒤 Git의 값으로 돌아오는지 확인한다.

```bash
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":100},"alternateBackends":[{"kind":"Service","name":"fraud-registry-production-predictor","weight":0}]}}'

oc get applications.argoproj.io jukebox-serving -n openshift-gitops -w
```

Self-heal 후 Route가 Git의 선언값으로 복구되면 완료다.

> GitOps Application을 삭제해도 기본값에서는 배포 리소스가 자동 삭제되지 않는다. `prune`과 finalizer를 사용하기 전에 삭제 범위를 반드시 확인한다.
