# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day10

> 사전 활성화: [Week1 Day1&2 - KServe RawDeployment 구성](<Week1-Day1&2-환경구성.md#kserve-rawdeployment-구성>), [Week2 Day7](<Week2-Day7 실습.md>)의 KFP Run, [Week2 Day8](<Week2-Day8 실습.md>)의 `fraud-kfp` Registry v1/v2와 `fraud-kfp-v1`·`fraud-kfp-v2` InferenceService를 먼저 완료한다. GitOps는 선택 기능이며 같은 문서의 [Tekton CI/CD와 Argo CD GitOps 구성](<Week1-Day1&2-환경구성.md#tekton-cicd와-argo-cd-gitops-구성>) 중 Argo CD만 필요하다.

Day7에서 훈련한 정확한 모델 artifact를 Day8에서 Registry에 등록한 뒤, Day10에서 현재 v1 트래픽을 새 v2로 점진적으로 전환한다. Day5의 `fraud-blue`, `fraud-green`, `fraud-route`는 사용하지 않는다.

```text
Day7 KFP fraud-n20 artifact
  -> Day8 Registry fraud-kfp:v1
  -> KServe fraud-kfp-v1
  -> 현재 운영 backend

Day7 KFP fraud-n200 artifact
  -> Day8 Registry fraud-kfp:v2
  -> KServe fraud-kfp-v2
  -> 신규 candidate backend

Day10 fraud-kfp-route
  -> v1 100:0 v2
  -> v1 90:10 v2
  -> v1 50:50 v2
  -> v1 0:100 v2
```

### 1. Day7 KFP Run lineage 확인
Day8의 lineage 파일이 있으면 불러온다. 새 Bastion 세션이라 파일이 없으면 Day8의 **KFP artifact를 서빙용 S3 경로로 승격** 절에서 값을 다시 만든다.

```bash
test -s /tmp/day8-lineage.env
source /tmp/day8-lineage.env

printf 'v1 KFP Run=%s (%s)\n' "$V1_RUN_NAME" "$V1_RUN_ID"
printf 'v2 KFP Run=%s (%s)\n' "$V2_RUN_NAME" "$V2_RUN_ID"

oc get workflows.argoproj.io -n jukebox -o json | jq -r \
  --arg v1 "$V1_RUN_ID" --arg v2 "$V2_RUN_ID" '
    .items[]
    | select(.metadata.labels["pipeline/runid"] == $v1 or
             .metadata.labels["pipeline/runid"] == $v2)
    | [.metadata.annotations["pipelines.kubeflow.org/run_name"],
       .metadata.labels["pipeline/runid"],
       .status.phase]
    | @tsv
  '
```

두 Run 모두 `Succeeded`이고 ID가 `/tmp/day8-lineage.env`와 일치해야 한다.

> Day10의 Registry 대상은 `fraud-kfp`다. 이전 실습의 `fraud-detection`이 `ARCHIVED`로 표시되더라도 다른 Registered Model이므로 이 전환 절차와 무관하다. `/tmp/day8-lineage.env`의 `REGISTERED_MODEL_ID`가 `fraud-kfp`를 가리키는지 다음 절에서 반드시 확인한다.

### 2. Registry, S3와 InferenceService 교차 확인
Registry Service를 port-forward한다.

```bash
oc port-forward -n rhoai-model-registries \
  svc/jukebox-registry 18080:8080
```

다른 Bastion 터미널에서 실행한다.

```bash
source /tmp/day8-lineage.env

REGISTERED_MODEL_NAME="$(
  curl -fsS \
    "http://127.0.0.1:18080/api/model_registry/v1alpha3/registered_models/${REGISTERED_MODEL_ID}" |
    jq -r '.name'
)"
test "$REGISTERED_MODEL_NAME" = "fraud-kfp"
printf 'Registered Model=%s (%s)\n' \
  "$REGISTERED_MODEL_NAME" "$REGISTERED_MODEL_ID"

curl -fsS \
  http://127.0.0.1:18080/api/model_registry/v1alpha3/model_versions |
  jq --arg id "$REGISTERED_MODEL_ID" '
    .items[]
    | select(.registeredModelId == $id)
    | select(.name == "v1" or .name == "v2")
    | {name, id, state, customProperties}
  '

for version in v1 v2; do
  oc get isvc "fraud-kfp-${version}" -n jukebox \
    -o jsonpath='{.metadata.name}{" "}{.metadata.annotations.modelregistry\.opendatahub\.io/model-version-id}{" "}{.spec.predictor.model.storageUri}{"\n"}'
done

printf 'expected v1 version=%s uri=s3://rhoai-models/%s\n' \
  "$V1_MODEL_VERSION_ID" "$V1_MODEL_PREFIX"
printf 'expected v2 version=%s uri=s3://rhoai-models/%s\n' \
  "$V2_MODEL_VERSION_ID" "$V2_MODEL_PREFIX"

test "$V1_SHA256" = "$(
  mc cat "truenas/rhoai-models/${V1_MODEL_PREFIX}/model.joblib" |
    sha256sum | awk '{print $1}'
)"
test "$V2_SHA256" = "$(
  mc cat "truenas/rhoai-models/${V2_MODEL_PREFIX}/model.joblib" |
    sha256sum | awk '{print $1}'
)"
```

이 검증은 다음 세 값이 같은 모델 버전을 가리키는지 확인한다.

1. Day7 KFP Run ID와 artifact
2. Day8 Registry Model Version ID, S3 URI와 SHA-256
3. KServe InferenceService annotation과 `storageUri`

### 3. v1/v2 직접 추론 재확인
```bash
oc get isvc fraud-kfp-v1 fraud-kfp-v2 -n jukebox

cat > /tmp/python3/fraud-kfp-request.json <<'EOF'
{
  "inputs": [
    {
      "name": "input-0",
      "shape": [1, 7],
      "datatype": "FP32",
      "data": [3672.37, 22.0, 1.0, 3.0, 440.0, 53.2, 0.0]
    }
  ]
}
EOF

oc port-forward -n jukebox \
  deploy/fraud-kfp-v1-predictor 18081:8080 >/tmp/fraud-kfp-v1-pf.log 2>&1 &
V1_PF=$!
oc port-forward -n jukebox \
  deploy/fraud-kfp-v2-predictor 18082:8080 >/tmp/fraud-kfp-v2-pf.log 2>&1 &
V2_PF=$!
sleep 3

V1_PREDICTION="$(
  curl -fsS -H 'Content-Type: application/json' \
    http://127.0.0.1:18081/v2/models/fraud/infer \
    -d @/tmp/python3/fraud-kfp-request.json |
    jq -r '.outputs[0].data[0]'
)"
V2_PREDICTION="$(
  curl -fsS -H 'Content-Type: application/json' \
    http://127.0.0.1:18082/v2/models/fraud/infer \
    -d @/tmp/python3/fraud-kfp-request.json |
    jq -r '.outputs[0].data[0]'
)"

kill "$V1_PF" "$V2_PF"
wait "$V1_PF" "$V2_PF" 2>/dev/null || true

printf 'v1=%s v2=%s\n' "$V1_PREDICTION" "$V2_PREDICTION"
```

검증한 데이터셋과 패키지 기준 예상값은 `v1=1 v2=0`이다. 두 값이 같더라도 Route 전환 자체는 가능하지만 응답 분포만으로 backend를 구분할 수 없으므로 Pod 요청 지표를 함께 확인해야 한다.

### 4. v1 기준 Route 생성
처음에는 기존 v1에 모든 트래픽을 보내고 v2는 0으로 시작한다.

```bash
oc apply -f - <<'EOF'
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: fraud-kfp-route
  namespace: jukebox
  labels:
    app.kubernetes.io/part-of: fraud-kfp
spec:
  to:
    kind: Service
    name: fraud-kfp-v1-predictor
    weight: 100
  alternateBackends:
    - kind: Service
      name: fraud-kfp-v2-predictor
      weight: 0
  port:
    targetPort: http
  wildcardPolicy: None
EOF

ROUTE="http://$(
  oc get route fraud-kfp-route -n jukebox -o jsonpath='{.spec.host}'
)"

oc get route fraud-kfp-route -n jukebox \
  -o jsonpath='{.spec.to.name}{"="}{.spec.to.weight}{" "}{range .spec.alternateBackends[*]}{.name}{"="}{.weight}{" "}{end}{"\n"}'
```

`oc get route` 출력은 `fraud-kfp-v1-predictor=100 fraud-kfp-v2-predictor=0`이어야 한다. 

```bash
curl -fsS -H 'Content-Type: application/json' \
  "$ROUTE/v2/models/fraud/infer" \
  -d @/tmp/python3/fraud-kfp-request.json | jq .
```

앞 절에서 확인한 것처럼 이 테스트 입력에 대해 v1이 `predict=1`, v2가 `predict=0`을 반환한다면 초기 Route의 응답은 `predict=1`이 정상이다.

### 5. v2 점진적 트래픽 전환
먼저 90:10으로 candidate에 일부 트래픽만 전달한다.

```bash
oc patch route fraud-kfp-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":90},"alternateBackends":[{"kind":"Service","name":"fraud-kfp-v2-predictor","weight":10}]}}'

# Router 설정 전파를 기다린 뒤 응답 비율을 확인한다.
sleep 10

for i in $(seq 1 40); do
  curl -fsS -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-kfp-request.json |
    jq -r '.outputs[0].data[0]'
done | sort | uniq -c
```

예상 prediction이 `v1=1`, `v2=0`이면 대략 `1`이 36회, `0`이 4회에 가깝게 나온다. 요청 수가 적으므로 정확히 90:10일 필요는 없다.

50:50으로 확대한다.

```bash
oc patch route fraud-kfp-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":50},"alternateBackends":[{"kind":"Service","name":"fraud-kfp-v2-predictor","weight":50}]}}'

sleep 10

for i in $(seq 1 40); do
  curl -fsS -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-kfp-request.json |
    jq -r '.outputs[0].data[0]'
done | sort | uniq -c
```

오류율, latency와 업무 품질에 이상이 없다는 가정으로 0:100 전환한다.

```bash
oc patch route fraud-kfp-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":0},"alternateBackends":[{"kind":"Service","name":"fraud-kfp-v2-predictor","weight":100}]}}'

sleep 10

for i in $(seq 1 10); do
  curl -fsS -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-kfp-request.json |
    jq -r '.outputs[0].data[0]'
done | sort | uniq -c
```

모든 응답이 v2 prediction이면 전환이 완료된 것이다.

### 즉시 롤백
v2 오류가 발견되면 새 배포를 삭제하지 않고 Route만 v1 100:0으로 되돌린다.

```bash
oc patch route fraud-kfp-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":100},"alternateBackends":[{"kind":"Service","name":"fraud-kfp-v2-predictor","weight":0}]}}'

sleep 10

oc get route fraud-kfp-route -n jukebox \
  -o jsonpath='{.spec.to.name}{"="}{.spec.to.weight}{" "}{range .spec.alternateBackends[*]}{.name}{"="}{.weight}{" "}{end}{"\n"}'
```

정상 전환을 완료한 경우에는 다시 0:100으로 적용하고 Registry v1의 custom property `stage`를 `Production`에서 `Archived`로 변경한다. Registry 기본 필드 `state=LIVE`는 삭제 목적이 아니므로 그대로 둔다.

### 참고: Registry 기본 state 변경
`state`는 `customProperties` 안의 값이 아니므로 property 편집 화면에 나타나지 않는다. Model Registry의 Registered Model과 Model Version이 가진 최상위 기본 필드이며, Kubernetes CR/YAML이 아니라 Registry REST API로 변경한다.

Day10에서는 롤백용 v1을 보존하므로 `stage=Archived`, `state=LIVE`에서 멈춘다. 이후 보존기간이 끝나 더 이상 활성 객체로 둘 필요가 없을 때만 다음 순서로 정리한다.

1. custom property `stage=Archived`와 필요한 metadata 수정이 끝났는지 확인한다.
2. 마지막으로 기본 `state`를 `ARCHIVED`로 변경한다.

`state=ARCHIVED`를 적용해도 `stage`는 자동으로 `Archived`가 되지 않는다. 반대로 `stage=Archived`도 기본 `state`를 변경하지 않는다. UI에서는 `state=ARCHIVED` 객체의 property 편집이 제한될 수 있으므로 반드시 property를 먼저 수정한다.

```bash
# Day10에서 확인한 v1 ID를 사용하되, 보존기간이 끝났을 때만 실행한다.
TARGET_MODEL_VERSION_ID="$V1_MODEL_VERSION_ID"

curl -fsS \
  "http://127.0.0.1:18080/api/model_registry/v1alpha3/model_versions/${TARGET_MODEL_VERSION_ID}" |
  jq '{id, name, registeredModelId, state, customProperties}'

curl -fsS -X PATCH \
  -H 'Content-Type: application/json' \
  "http://127.0.0.1:18080/api/model_registry/v1alpha3/model_versions/${TARGET_MODEL_VERSION_ID}" \
  -d '{"state":"ARCHIVED"}' | jq '{id, name, state}'
```

Registered Model 전체를 더 이상 사용하지 않을 때는 각 Model Version의 정리 상태를 확인한 후 별도 endpoint를 사용한다.

```bash
TARGET_REGISTERED_MODEL_ID="$REGISTERED_MODEL_ID"

curl -fsS -X PATCH \
  -H 'Content-Type: application/json' \
  "http://127.0.0.1:18080/api/model_registry/v1alpha3/registered_models/${TARGET_REGISTERED_MODEL_ID}" \
  -d '{"state":"ARCHIVED"}' | jq '{id, name, state}'
```

`ARCHIVED`를 `LIVE`로 되돌릴 때는 같은 요청의 payload를 `{"state":"LIVE"}`로 바꾼다. Registered Model과 각 Model Version의 `state`는 독립적이므로 상위 모델 하나만 바꿨다고 모든 버전이 자동 변경된다고 가정하지 않는다.

### 6. GitOps Operator 확인
GitOps는 RHOAI `aipipelines`가 사용하는 Argo Workflows와 다른 제품이다. Day10 기본 Route 전환에는 Tekton이 필요하지 않다.

```bash
oc get subscription -A | grep openshift-gitops-operator
oc get pods -n openshift-gitops
oc get crd applications.argoproj.io
```

기본 `openshift-gitops` Argo CD가 `jukebox` Namespace를 관리하도록 설정한다. 이 label은 Application Controller에 해당 Namespace의 관리 권한을 부여하므로 운영에서는 별도 Argo CD 인스턴스와 축소된 ClusterRole을 검토한다.

```bash
oc label namespace jukebox \
  argocd.argoproj.io/managed-by=openshift-gitops --overwrite

ARGO_SA=system:serviceaccount:openshift-gitops:openshift-gitops-argocd-application-controller

oc auth can-i create inferenceservices.serving.kserve.io \
  -n jukebox --as="$ARGO_SA"
oc auth can-i patch routes.route.openshift.io \
  -n jukebox --as="$ARGO_SA"
```

두 명령이 모두 `yes`여야 한다.

### GitOps 저장소 준비
Day6에서 만든 `hands-on` 조직에 비공개 `day10` 저장소를 만들고 현재 v1/v2 InferenceService와 Route를 선언 파일로 저장한다. Gitea 저장소 이름은 조직 안에서만 고유하면 되므로 기존 `hands-on/day06`과 충돌하지 않는다.

```text
day10/
├── kustomization.yaml
├── fraud-kfp-v1.json
├── fraud-kfp-v2.json
└── fraud-kfp-route.json
```

```bash
mkdir -p /tmp/day10
cd /tmp/day10

cat > kustomization.yaml <<'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - fraud-kfp-v1.json
  - fraud-kfp-v2.json
  - fraud-kfp-route.json
EOF

for version in v1 v2; do
  oc get isvc "fraud-kfp-${version}" -n jukebox -o json | jq \
    'del(.metadata.creationTimestamp, .metadata.generation,
         .metadata.resourceVersion, .metadata.uid, .metadata.ownerReferences,
         .metadata.finalizers,
         .metadata.annotations["kubectl.kubernetes.io/last-applied-configuration"],
         .status)' > "fraud-kfp-${version}.json"
done

oc get route fraud-kfp-route -n jukebox -o json | jq \
  'del(.metadata.creationTimestamp, .metadata.generation,
       .metadata.resourceVersion, .metadata.uid,
       .metadata.annotations["kubectl.kubernetes.io/last-applied-configuration"],
       .metadata.annotations["openshift.io/host.generated"],
       .status)' > fraud-kfp-route.json

oc kustomize . >/tmp/day10-rendered.yaml
oc apply --dry-run=server -f /tmp/day10-rendered.yaml
```

검토 후 저장소에 push한다. 인증정보는 remote URL에 직접 넣지 않는다. 이 홈랩의 Gitea는 별도 Route 인증서를 지정하지 않고 OCP 기본 Ingress 인증서를 사용하므로, Router가 제시하는 leaf 인증서가 아니라 이를 서명한 Ingress CA를 추출해 검증에 사용한다.

```bash
GITEA_HOST=$(oc get route gitea -n gitea -o jsonpath='{.spec.host}')
TLS_WORKDIR=$(mktemp -d)

oc get secret router-certs-default -n openshift-ingress -o json |
  jq -r '.data["tls.crt"]' | base64 -d \
  > "$TLS_WORKDIR/router-chain.pem"

# Router 인증서 체인에서 CA:TRUE인 인증서만 분리한다.
awk -v dir="$TLS_WORKDIR" '
  /-----BEGIN CERTIFICATE-----/ {cert=""}
  {cert=cert $0 ORS}
  /-----END CERTIFICATE-----/ {
    n++
    file=dir "/cert-" n ".pem"
    printf "%s", cert > file
    close(file)
  }
' "$TLS_WORKDIR/router-chain.pem"

: > "$TLS_WORKDIR/ingress-ca.pem"
for cert in "$TLS_WORKDIR"/cert-*.pem; do
  if openssl x509 -in "$cert" -noout -text | grep -q 'CA:TRUE'; then
    cat "$cert" >> "$TLS_WORKDIR/ingress-ca.pem"
  fi
done

test -s "$TLS_WORKDIR/ingress-ca.pem"
openssl x509 -in "$TLS_WORKDIR/ingress-ca.pem" \
  -noout -subject -issuer -dates
```

```bash
git init
git add .
git commit -m 'Manage Day 10 KFP model rollout'
git branch -M main
git remote add origin \
  https://gitea.apps.sno.ocp422.com/hands-on/day10.git
git -c http.sslCAInfo="$TLS_WORKDIR/ingress-ca.pem" \
  push -u origin main
```

### OCP Ingress CA를 Argo CD에 등록
Argo CD는 HTTPS Git 서버의 사용자 인증과 TLS 서버 인증을 별도로 처리한다. 다음 명령은 OCP Ingress CA를 Gitea 호스트 이름의 값으로 `argocd-tls-certs-cm`에 추가한다. 인증서 검증을 끄는 `insecure` 설정은 사용하지 않는다.

```bash
TLS_PATCH=$(jq -n \
  --arg host "$GITEA_HOST" \
  --rawfile ca "$TLS_WORKDIR/ingress-ca.pem" \
  '{data:{($host):$ca}}')

oc patch configmap argocd-tls-certs-cm \
  -n openshift-gitops --type=merge -p "$TLS_PATCH"

oc rollout restart deployment/openshift-gitops-repo-server \
  -n openshift-gitops
oc rollout status deployment/openshift-gitops-repo-server \
  -n openshift-gitops --timeout=180s

oc get configmap argocd-tls-certs-cm -n openshift-gitops \
  -o json | jq -r '.data | keys[]'
```

출력에 `gitea.apps.sno.ocp422.com`이 있어야 한다. 동일 Gitea 서버의 다른 저장소에도 이 CA 신뢰 설정이 공통 적용된다. OCP 기본 Ingress CA가 교체되면 같은 절차로 값을 갱신한다. Argo CD 공식 문서도 자체 서명 또는 사설 CA를 사용하는 HTTPS 저장소에는 서버 인증서나 발급 CA를 `argocd-tls-certs-cm`에 등록하는 방식을 권장한다: [Argo CD Private Repositories](https://argo-cd.readthedocs.io/en/latest/user-guide/private-repositories/#self-signed--untrusted-tls-certificates)

### 비공개 Git 저장소 인증 Secret
Gitea 사용자 설정의 `Applications`에서 `read:repository` 권한만 가진 PAT를 발급한다. PAT 값은 생성 직후 한 번만 확인할 수 있으므로 `<GITEA_PAT>` 자리에 직접 입력하고 문서나 Git 저장소에는 기록하지 않는다.

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
  url: https://gitea.apps.sno.ocp422.com/hands-on/day10.git
  username: <GITEA_ID>
  password: <GITEA_PAT>
EOF
```

CA는 ConfigMap, 사용자 인증정보는 Secret으로 분리된다. Secret에서 `insecure` 필드가 없어야 TLS 인증서 검증이 유지된다.

### Argo CD Application 생성
처음에는 `prune: false`로 두고 관리 범위를 확인한다.

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
    repoURL: https://gitea.apps.sno.ocp422.com/hands-on/day10.git
    targetRevision: main
    # 선언 파일이 저장소 루트에 있으므로 현재 디렉터리를 사용한다.
    path: .
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

oc get applications.argoproj.io jukebox-serving \
  -n openshift-gitops -w
```

`SYNC=Synced`, `HEALTH=Healthy`가 되면 `Ctrl+C`로 종료한다.

`SYNC=Unknown`이 계속되면 조건과 repo-server 로그를 확인한다.

```bash
oc get applications.argoproj.io jukebox-serving -n openshift-gitops \
  -o json | jq '{sync:.status.sync.status,
    health:.status.health.status,
    conditions:(.status.conditions // [])}'

oc logs deployment/openshift-gitops-repo-server \
  -n openshift-gitops --tail=200 | \
  grep -E 'x509|Unauthorized|authentication required|failed to list refs'
```

- `x509: certificate signed by unknown authority`: Gitea 호스트 키 또는 Ingress CA 등록을 다시 확인한다.
- `authentication required: Unauthorized`: repository Secret의 URL, ID, PAT와 PAT의 `read:repository` 권한을 확인한다.
- 정상 상태에서는 `conditions`가 빈 배열이고 Application과 세 관리 리소스가 모두 `Synced/Healthy`다.

### GitOps 동작과 self-heal 검증
1. Git의 Route weight를 `0:100`에서 `50:50`으로 변경하고 push한다.
2. Argo CD가 클러스터 Route를 `50:50`으로 변경하는지 확인한다.
3. 클러스터에서 직접 `100:0`으로 patch한다.
4. `selfHeal`이 Git의 `50:50`으로 복구하는지 확인한다.

```bash
# Route 선언을 수정한 Git 작업 디렉터리에서 실행한다.
git add fraud-kfp-route.json
git commit -m 'Change Day 10 route weight to 50:50'
git -c http.sslCAInfo="$TLS_WORKDIR/ingress-ca.pem" push

# Git push 후 기본 refresh 주기를 기다리거나 즉시 새 revision을 확인시킨다.
oc annotate applications.argoproj.io jukebox-serving \
  -n openshift-gitops argocd.argoproj.io/refresh=hard --overwrite

oc get applications.argoproj.io jukebox-serving -n openshift-gitops \
  -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status

oc patch route fraud-kfp-route -n jukebox --type=merge \
  -p '{"spec":{"to":{"weight":100},"alternateBackends":[{"kind":"Service","name":"fraud-kfp-v2-predictor","weight":0}]}}'

oc get applications.argoproj.io jukebox-serving -n openshift-gitops -w
```

Self-heal 후 Route가 Git 선언값으로 복구되면 완료다.

```bash
rm -rf "$TLS_WORKDIR"
unset TLS_WORKDIR TLS_PATCH GITEA_HOST
```

> Application을 삭제해도 `prune: false`이고 리소스 삭제 finalizer가 없으면 기존 InferenceService와 Route는 자동 삭제되지 않는다.

### 최종 확인
```bash
oc get workflows.argoproj.io -n jukebox
oc get isvc fraud-kfp-v1 fraud-kfp-v2 -n jukebox
oc get route fraud-kfp-route -n jukebox
oc get applications.argoproj.io jukebox-serving -n openshift-gitops
```

최종적으로 Day7 KFP Run ID, Day8 Registry Version ID, S3 SHA-256, Day10 InferenceService annotation과 Git 선언을 같은 버전까지 역추적할 수 있어야 한다.

### 선택 정리
Day15에서 다시 사용할 경우 v1/v2 InferenceService, Route와 Registry metadata를 유지한다. Day10까지만 반복 실습하고 리소스를 비우려면 GitOps Application을 먼저 삭제한 뒤 서빙 리소스를 제거한다.

```bash
oc delete application jukebox-serving -n openshift-gitops \
  --ignore-not-found
oc delete secret day10-gitops-repository -n openshift-gitops \
  --ignore-not-found
oc delete route fraud-kfp-route -n jukebox --ignore-not-found
oc delete isvc fraud-kfp-v1 fraud-kfp-v2 -n jukebox \
  --ignore-not-found --wait=true --timeout=5m
```

Registry `fraud-kfp` metadata와 `rhoai-models/fraud-kfp/` artifact까지 제거하려면 더 이상 Day15에서 사용하지 않는지 확인한 뒤 대시보드에서 Registered Model을 삭제하고 MinIO prefix를 삭제한다.
