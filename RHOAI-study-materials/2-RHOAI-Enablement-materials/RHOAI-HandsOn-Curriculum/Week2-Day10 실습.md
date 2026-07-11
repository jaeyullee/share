# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day10

Day6~9의 훈련, Registry, KServe, RBAC 흐름을 하나로 연결한다. 기본 E2E는 수동으로 수행하고, OpenShift GitOps가 설치된 환경에서는 InferenceService와 Route를 GitOps로 관리한다.

### 사전 상태 확인
```bash
oc get dspa -n jukebox
oc get modelregistry -n rhoai-model-registries
oc get servingruntime,isvc,route -n jukebox
mc stat truenas/rhoai-models/fraud/model.joblib
mc stat truenas/rhoai-models/fraud-v2/model.joblib
```

### E2E 수동 경로
1. Day7 KFP Pipeline Run으로 모델을 훈련하고 평가 지표를 확인한다.
2. Day8 Model Registry에 v1과 v2를 등록하고 v2를 `stage=Production`으로 승격한다.
3. Registry의 Production 버전 S3 URI로 `fraud-registry-production` InferenceService를 배포한다.
4. 추론 요청에 정상 응답하는지 확인한다.
5. Day5의 `fraud-route` weight를 이용해 기존 버전에서 새 버전으로 전환한다.

```bash
oc wait --for=condition=Ready \
  isvc/fraud-registry-production -n jukebox --timeout=300s

oc get isvc fraud-registry-production -n jukebox
oc get route fraud-route -n jukebox -o yaml
```

### GitOps Operator 확인
GitOps는 RHOAI `aipipelines`의 Argo Workflows와 다른 제품이다.

```bash
oc get subscription -A | grep openshift-gitops-operator
oc get pods -n openshift-gitops
oc get crd applications.argoproj.io
```

설치되어 있지 않으면 미러 CatalogSource의 `openshift-gitops-operator` 패키지를 별도로 설치한다.

### GitOps 저장소 준비
내부 Git 서버에 `rhoai-lab/day10-gitops` 저장소를 만들고 아래 구조로 배포 YAML을 저장한다.

```text
day10-gitops/
└── serving/
    ├── kustomization.yaml
    ├── inferenceservice.yaml
    └── route.yaml
```

```bash
mkdir -p /tmp/day10-gitops/serving
cd /tmp/day10-gitops/serving

cat > kustomization.yaml <<'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - inferenceservice.yaml
  - route.yaml
EOF

oc get isvc fraud-blue -n jukebox -o yaml | \
  yq 'del(.metadata.creationTimestamp, .metadata.generation, .metadata.resourceVersion, .metadata.uid, .metadata.ownerReferences, .status)' \
  > inferenceservice.yaml

oc get route fraud-route -n jukebox -o yaml | \
  yq 'del(.metadata.creationTimestamp, .metadata.resourceVersion, .metadata.uid, .status)' \
  > route.yaml
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
저장소가 공개라면 이 Secret은 필요 없다. 비공개 저장소일 때만 생성한다.

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

oc get application jukebox-serving -n openshift-gitops
oc describe application jukebox-serving -n openshift-gitops
```

### GitOps 동작 검증
1. Route weight를 Git에서 `90:10`에서 `50:50`으로 변경하고 push한다.
2. Argo CD Application이 `Synced`와 `Healthy`가 되는지 확인한다.
3. 클러스터 Route에 변경된 weight가 반영됐는지 확인한다.

```bash
oc get application jukebox-serving -n openshift-gitops \
  -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status

oc get route fraud-route -n jukebox \
  -o jsonpath='{.spec.to.name}{"="}{.spec.to.weight}{" "}{range .spec.alternateBackends[*]}{.name}{"="}{.weight}{" "}{end}{"\n"}'
```

### Self-heal 검증
클러스터에서 Route weight를 직접 바꾼 뒤 Git의 값으로 돌아오는지 확인한다.

```bash
oc patch route fraud-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":100},"alternateBackends":[{"kind":"Service","name":"fraud-green-predictor","weight":0}]}}'

oc get application jukebox-serving -n openshift-gitops -w
```

Self-heal 후 Route가 Git의 선언값으로 복구되면 완료다.

> GitOps Application을 삭제해도 기본값에서는 배포 리소스가 자동 삭제되지 않는다. `prune`과 finalizer를 사용하기 전에 삭제 범위를 반드시 확인한다.

