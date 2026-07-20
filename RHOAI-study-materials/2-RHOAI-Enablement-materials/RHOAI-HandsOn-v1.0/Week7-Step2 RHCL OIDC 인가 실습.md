# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 실습
## week 7 - Step 2 RHBK JWT와 RHCL OIDC 인가

> **기능 상태를 구분한다.** RHCL 1.4의 `AuthPolicy`를 이용한 OIDC 인증·인가는 정식 지원 기능이다. 다만 이 환경에서 사용하는 RHCL 1.4.1 disconnected 설치 절차는 Technology Preview(TP)이며, RHOAI 3.4 MaaS external OIDC도 별도 TP 기능이다. 필수 실습과 선택 실습의 지원 범위를 혼동하지 않는다.
> [Disconnected installation is a Technology Preview feature only.](https://docs.redhat.com/en/documentation/red_hat_connectivity_link/1.4/html/installing_connectivity_link/rhcl-install-disconnected)

> **사전 활성화:** [Week3 Day14](<Week3-Day14 실습.md>)의 RHCL operand와 MaaS, [Week7 Step 1](<Week7-Step1 RHBK OIDC 실습.md>)의 RHBK `rhoai` realm, `openshift` client, 사용자·그룹과 `groups` mapper가 남아 있어야 한다. Step 1의 `KeycloakRealmImport`는 삭제해도 되지만 `### 원복`은 아직 실행하지 않는다. Step2에서 새 Operator를 설치하지 않는다.

### 실습 목표

1. RHBK JWT의 서명, issuer와 `groups` claim을 RHCL Authorino가 검증한다.
2. RHCL `AuthPolicy`를 `HTTPRoute`에 연결해 미인증 `401`, 허용 그룹 `200`, 비허용 그룹 `403`을 확인한다.
3. 선택 실습에서는 OpenShift `User`가 없는 RHBK 사용자도 MaaS external OIDC로 인증되고, token group에 해당하는 모델만 조회되는 TP 경로를 확인한다.

```text
RHBK access token
  -> OpenShift Route(passthrough TLS)
  -> Gateway + HTTPRoute
  -> RHCL AuthPolicy / Authorino
     -> JWT 검증
     -> groups 기반 인가
  -> echo Service

[선택 TP]
RHBK 전용 사용자 token
  -> MaaS Gateway
  -> Tenant.spec.externalOIDC
  -> MaaSSubscription의 group과 token groups 비교
  -> 허용된 모델 목록
```

### 사전점검과 Step2 백업

RHBK, RHCL과 MaaS가 준비됐는지 확인한다. 선택 TP를 수행하지 않아도 RHCL operand는 모두 Ready여야 한다.

```bash
oc wait keycloak/week7-rhbk -n week7-rhbk \
  --for=condition=Ready --timeout=300s
oc wait kuadrant/kuadrant -n kuadrant-system \
  --for=condition=Ready --timeout=300s
oc wait authorino/authorino -n kuadrant-system \
  --for=condition=Ready --timeout=300s
oc wait limitador/limitador -n kuadrant-system \
  --for=condition=Ready --timeout=300s

oc get gatewayclass data-science-gateway-class \
  -o jsonpath='{.status.conditions[?(@.type=="Accepted")].status}{"\n"}'
oc get tenant default-tenant -n models-as-a-service
curl -skf https://maas.apps.sno.ocp422.com/maas-api/health | jq .
```

GatewayClass 출력은 `True`, Tenant는 `READY=True`, MaaS health는 `healthy`여야 한다.

Step2 전용 백업 경로를 만든다. SSH를 다시 접속해 shell 변수가 사라져도 찾을 수 있도록 활성 경로 파일도 함께 기록한다.

```bash
WEEK7_STEP2_BACKUP_DIR="/tmp/week7-step2-before-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$WEEK7_STEP2_BACKUP_DIR"
chmod 700 "$WEEK7_STEP2_BACKUP_DIR"

oc get authorino authorino -n kuadrant-system -o json \
  > "$WEEK7_STEP2_BACKUP_DIR/authorino.json"
oc get tenant default-tenant -n models-as-a-service -o json \
  > "$WEEK7_STEP2_BACKUP_DIR/tenant.json"

printf '%s\n' "$WEEK7_STEP2_BACKUP_DIR" \
  > /tmp/week7-step2-active-backup
printf 'Using WEEK7_STEP2_BACKUP_DIR=%s\n' "$WEEK7_STEP2_BACKUP_DIR"
ls -l "$WEEK7_STEP2_BACKUP_DIR"
```

### RHBK issuer와 CA 준비

```bash
APPS_DOMAIN="$(oc get ingress.config cluster -o jsonpath='{.spec.domain}')"
RHBK_HOST="week7-rhbk.${APPS_DOMAIN}"
RHBK_ISSUER="https://${RHBK_HOST}/realms/rhoai"
RHCL_HOST="week7-rhcl-authz.${APPS_DOMAIN}"

RHBK_CA_FILE="$(mktemp)"
chmod 600 "$RHBK_CA_FILE"
oc get secret week7-rhbk-tls -n week7-rhbk \
  -o jsonpath='{.data.ca\.crt}' | base64 -d > "$RHBK_CA_FILE"

curl --cacert "$RHBK_CA_FILE" -fsS \
  "${RHBK_ISSUER}/.well-known/openid-configuration" | \
  jq -e --arg issuer "$RHBK_ISSUER" '.issuer == $issuer'
```

Authorino가 기존에 신뢰하던 CA bundle을 읽고 RHBK CA를 추가한다. `/etc/ssl/certs` 전체를 ConfigMap으로 덮으면 `ca-bundle.crt` symlink가 끊어지므로 사용하지 않는다.

```bash
BASE_CA_FILE="$(mktemp)"
WEEK7_CA_FILE="$(mktemp)"
chmod 600 "$BASE_CA_FILE" "$WEEK7_CA_FILE"

oc exec -n kuadrant-system deployment/authorino -- \
  cat /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
  > "$BASE_CA_FILE"
test -s "$BASE_CA_FILE"

cat "$BASE_CA_FILE" "$RHBK_CA_FILE" > "$WEEK7_CA_FILE"

oc create configmap authorino-week7-ca -n kuadrant-system \
  --from-file=tls-ca-bundle.pem="$WEEK7_CA_FILE" \
  --dry-run=client -o yaml | oc apply -f -

oc patch authorino authorino -n kuadrant-system --type=merge -p '
{"spec":{"volumes":{"defaultMode":420,"items":[{
  "name":"week7-combined-ca",
  "mountPath":"/etc/pki/ca-trust/extracted/pem",
  "configMaps":["authorino-week7-ca"],
  "items":[{"key":"tls-ca-bundle.pem","path":"tls-ca-bundle.pem"}]
}]}}}'

oc rollout status deployment/authorino \
  -n kuadrant-system --timeout=300s

oc exec -n kuadrant-system deployment/authorino -- \
  curl -fsS "${RHBK_ISSUER}/.well-known/openid-configuration" | \
  jq -e --arg issuer "$RHBK_ISSUER" '.issuer == $issuer'

rm -f "$BASE_CA_FILE" "$WEEK7_CA_FILE"
unset BASE_CA_FILE WEEK7_CA_FILE
```

### HTTPS backend와 Gateway 생성

검증용 backend는 CPU Workbench image의 Python 표준 라이브러리만 사용한다. RHBK token을 평문 HTTP로 보내지 않도록 Gateway에서 TLS를 종료하고 OpenShift Route는 passthrough로 연결한다.

```bash
oc create namespace week7-rhcl-authz \
  --dry-run=client -o yaml | oc apply -f -

ECHO_IMAGE="$(oc get imagestreamtag s2i-minimal-notebook:3.4 \
  -n redhat-ods-applications \
  -o jsonpath='{.image.dockerImageReference}')"

TLS_KEY_FILE="$(mktemp)"
TLS_CERT_FILE="$(mktemp)"
chmod 600 "$TLS_KEY_FILE" "$TLS_CERT_FILE"
openssl req -x509 -newkey rsa:2048 -nodes -days 2 \
  -keyout "$TLS_KEY_FILE" -out "$TLS_CERT_FILE" \
  -subj "/CN=${RHCL_HOST}" \
  -addext "subjectAltName=DNS:${RHCL_HOST}"

oc create secret tls week7-rhcl-tls -n week7-rhcl-authz \
  --key="$TLS_KEY_FILE" --cert="$TLS_CERT_FILE"
rm -f "$TLS_KEY_FILE" "$TLS_CERT_FILE"
unset TLS_KEY_FILE TLS_CERT_FILE
```

```bash
oc apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo
  namespace: week7-rhcl-authz
spec:
  replicas: 1
  selector:
    matchLabels:
      app: echo
  template:
    metadata:
      labels:
        app: echo
    spec:
      containers:
        - name: echo
          image: ${ECHO_IMAGE}
          command: ["python3", "-c"]
          args:
            - |
              from http.server import BaseHTTPRequestHandler, HTTPServer
              class Handler(BaseHTTPRequestHandler):
                  def do_GET(self):
                      body = b"week7-rhcl-authz-ok\n"
                      self.send_response(200)
                      self.send_header("Content-Type", "text/plain")
                      self.send_header("Content-Length", str(len(body)))
                      self.end_headers()
                      self.wfile.write(body)
                  def log_message(self, *args):
                      pass
              HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
          ports:
            - name: http
              containerPort: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: echo
  namespace: week7-rhcl-authz
spec:
  selector:
    app: echo
  ports:
    - name: http
      port: 8080
      targetPort: http
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: week7-rhcl-authz
  namespace: week7-rhcl-authz
  annotations:
    networking.istio.io/service-type: ClusterIP
spec:
  gatewayClassName: data-science-gateway-class
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: ${RHCL_HOST}
      tls:
        mode: Terminate
        certificateRefs:
          - kind: Secret
            name: week7-rhcl-tls
      allowedRoutes:
        namespaces:
          from: Same
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: week7-rhcl-authz
  namespace: week7-rhcl-authz
spec:
  parentRefs:
    - name: week7-rhcl-authz
  hostnames:
    - ${RHCL_HOST}
  rules:
    - backendRefs:
        - name: echo
          port: 8080
EOF

oc rollout status deployment/echo \
  -n week7-rhcl-authz --timeout=300s
```

Gateway가 만든 Service 이름을 status에서 읽어 passthrough Route를 만든다.

```bash
for i in $(seq 1 60); do
  GW_SERVICE="$(oc get gateway week7-rhcl-authz \
    -n week7-rhcl-authz \
    -o jsonpath='{.status.addresses[0].value}' 2>/dev/null | \
    cut -d. -f1)"
  test -n "$GW_SERVICE" && \
    oc get service "$GW_SERVICE" -n week7-rhcl-authz \
      >/dev/null 2>&1 && break
  sleep 2
done
test -n "$GW_SERVICE"

oc create route passthrough week7-rhcl-authz \
  -n week7-rhcl-authz \
  --service="$GW_SERVICE" \
  --port=https \
  --hostname="$RHCL_HOST"

oc get gateway,httproute -n week7-rhcl-authz

for i in $(seq 1 60); do
  PRE_POLICY_BODY="$(curl -sk "https://${RHCL_HOST}/" 2>/dev/null || true)"
  test "$PRE_POLICY_BODY" = 'week7-rhcl-authz-ok' && break
  sleep 2
done
test "$PRE_POLICY_BODY" = 'week7-rhcl-authz-ok'
printf 'pre_policy_body=%s\n' "$PRE_POLICY_BODY"
```

정책 적용 전에는 `week7-rhcl-authz-ok`가 반환된다.

### RHCL AuthPolicy 적용

인가 pattern은 `patternMatching.patterns`에 직접 작성한다. RHCL 1.4.1 스키마에 없는 별도 named pattern 필드를 사용하면 API 서버가 해당 필드를 제거할 수 있다.

```bash
oc apply -f - <<EOF
apiVersion: kuadrant.io/v1
kind: AuthPolicy
metadata:
  name: week7-rhcl-authz
  namespace: week7-rhcl-authz
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: week7-rhcl-authz
  rules:
    authentication:
      oidc:
        jwt:
          issuerUrl: ${RHBK_ISSUER}
    authorization:
      allow-week7-users:
        patternMatching:
          patterns:
            - selector: auth.identity.groups
              operator: incl
              value: rhoai-week7-users
EOF

for i in $(seq 1 60); do
  ACCEPTED="$(oc get authpolicy week7-rhcl-authz \
    -n week7-rhcl-authz \
    -o jsonpath='{.status.conditions[?(@.type=="Accepted")].status}' \
    2>/dev/null || true)"
  ENFORCED="$(oc get authpolicy week7-rhcl-authz \
    -n week7-rhcl-authz \
    -o jsonpath='{.status.conditions[?(@.type=="Enforced")].status}' \
    2>/dev/null || true)"
  test "${ACCEPTED}/${ENFORCED}" = 'True/True' && break
  sleep 2
done
test "${ACCEPTED}/${ENFORCED}" = 'True/True'
oc get authpolicy week7-rhcl-authz -n week7-rhcl-authz -o yaml | \
  sed -n '/status:/,$p'
```

### 401, 200, 403 검증

Step1 Secret에서 두 사용자의 비밀번호와 client secret을 읽되 출력하지 않는다.

```bash
CLIENT_SECRET="$(oc get secret week7-rhbk-realm-secrets \
  -n week7-rhbk -o jsonpath='{.data.CLIENT_SECRET}' | base64 -d)"
ADMIN_PASSWORD="$(oc get secret week7-rhbk-realm-secrets \
  -n week7-rhbk -o jsonpath='{.data.ADMIN_PASSWORD}' | base64 -d)"
USER_PASSWORD="$(oc get secret week7-rhbk-realm-secrets \
  -n week7-rhbk -o jsonpath='{.data.USER_PASSWORD}' | base64 -d)"

get_rhbk_token() {
  curl --cacert "$RHBK_CA_FILE" -fsS \
    -d grant_type=password \
    -d client_id=openshift \
    --data-urlencode client_secret="$CLIENT_SECRET" \
    --data-urlencode username="$1" \
    --data-urlencode password="$2" \
    "${RHBK_ISSUER}/protocol/openid-connect/token" | \
    jq -er '.access_token'
}

USER_TOKEN="$(get_rhbk_token rhoai-week7-user "$USER_PASSWORD")"
ADMIN_TOKEN="$(get_rhbk_token rhoai-week7-admin "$ADMIN_PASSWORD")"
```

```bash
for i in $(seq 1 60); do
  NO_TOKEN_CODE="$(curl -sk -o /dev/null -w '%{http_code}' \
    "https://${RHCL_HOST}/")"

  USER_CODE="$(curl -sk -o /tmp/week7-rhcl-user.out -w '%{http_code}' \
    -H "Authorization: Bearer ${USER_TOKEN}" \
    "https://${RHCL_HOST}/")"

  ADMIN_CODE="$(curl -sk -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    "https://${RHCL_HOST}/")"

  test "${NO_TOKEN_CODE}/${USER_CODE}/${ADMIN_CODE}" = \
    '401/200/403' && break
  sleep 2
done

printf 'no_token=%s\nallowed_user=%s body=' \
  "$NO_TOKEN_CODE" "$USER_CODE"
cat /tmp/week7-rhcl-user.out
printf 'disallowed_admin=%s\n' "$ADMIN_CODE"

test "${NO_TOKEN_CODE}/${USER_CODE}/${ADMIN_CODE}" = '401/200/403'
rm -f /tmp/week7-rhcl-user.out
```

검증된 결과는 다음과 같다.

| 요청 | token group | 결과 |
|---|---|---|
| token 없음 | 없음 | `401` |
| `rhoai-week7-user` | `rhoai-week7-users` | `200`, `week7-rhcl-authz-ok` |
| `rhoai-week7-admin` | `rhods-admins` | `403` |

## 선택 TP: MaaS external OIDC

> 이 절은 RHOAI 3.4 Technology Preview다. 운영 적용 판단의 근거로 사용하지 않는다. 외부 OIDC 사용자는 Dashboard가 아니라 API로 MaaS를 사용한다.

### MaaS 상태와 external OIDC 적용

```bash
curl -skf https://maas.apps.sno.ocp422.com/maas-api/health | jq .
oc get tenant default-tenant -n models-as-a-service

oc patch tenant default-tenant -n models-as-a-service \
  --type=merge -p "$(jq -n \
    --arg issuer "$RHBK_ISSUER" \
    '{spec:{externalOIDC:{issuerUrl:$issuer,clientId:"openshift"}}}')"

for i in $(seq 1 60); do
  OIDC_ISSUER="$(oc get authpolicy maas-api-auth-policy \
    -n redhat-ods-applications -o json | \
    jq -r '.spec.rules.authentication["oidc-identities"].jwt.issuerUrl // empty')"
  test "$OIDC_ISSUER" = "$RHBK_ISSUER" && break
  sleep 2
done
test "$OIDC_ISSUER" = "$RHBK_ISSUER"
oc get tenant default-tenant -n models-as-a-service -o yaml | \
  sed -n '/externalOIDC:/,+4p'
```

### OpenShift 계정이 없는 RHBK 전용 사용자 생성

RHBK Admin REST API로 Step2 전용 사용자를 만들고 `rhoai-week7-users`에 넣는다. 비밀번호는 현재 shell에만 둔다.

```bash
RHBK_ADMIN_USER="$(oc get secret week7-rhbk-initial-admin \
  -n week7-rhbk -o jsonpath='{.data.username}' | base64 -d)"
RHBK_ADMIN_PASSWORD="$(oc get secret week7-rhbk-initial-admin \
  -n week7-rhbk -o jsonpath='{.data.password}' | base64 -d)"

RHBK_ADMIN_TOKEN="$(curl --cacert "$RHBK_CA_FILE" -fsS \
  -d grant_type=password \
  -d client_id=admin-cli \
  --data-urlencode username="$RHBK_ADMIN_USER" \
  --data-urlencode password="$RHBK_ADMIN_PASSWORD" \
  "https://${RHBK_HOST}/realms/master/protocol/openid-connect/token" | \
  jq -er '.access_token')"

EXTERNAL_USERNAME='rhoai-week7-external'
EXTERNAL_PASSWORD="$(openssl rand -hex 20)"

EXISTING_ID="$(curl --cacert "$RHBK_CA_FILE" -fsS \
  -H "Authorization: Bearer ${RHBK_ADMIN_TOKEN}" \
  "https://${RHBK_HOST}/admin/realms/rhoai/users?username=${EXTERNAL_USERNAME}&exact=true" | \
  jq -r '.[0].id // empty')"
test -z "$EXISTING_ID"

USER_JSON="$(jq -n --arg u "$EXTERNAL_USERNAME" --arg p "$EXTERNAL_PASSWORD" '{
  username:$u, enabled:true,
  firstName:"RHOAI", lastName:"External",
  email:($u + "@example.invalid"), emailVerified:true,
  requiredActions:[],
  credentials:[{type:"password",value:$p,temporary:false}]
}')"

test "$(curl --cacert "$RHBK_CA_FILE" -sS -o /dev/null -w '%{http_code}' \
  -X POST \
  -H "Authorization: Bearer ${RHBK_ADMIN_TOKEN}" \
  -H 'Content-Type: application/json' \
  "https://${RHBK_HOST}/admin/realms/rhoai/users" \
  -d "$USER_JSON")" = 201

EXTERNAL_USER_ID="$(curl --cacert "$RHBK_CA_FILE" -fsS \
  -H "Authorization: Bearer ${RHBK_ADMIN_TOKEN}" \
  "https://${RHBK_HOST}/admin/realms/rhoai/users?username=${EXTERNAL_USERNAME}&exact=true" | \
  jq -er '.[0].id')"

EXTERNAL_GROUP_ID="$(curl --cacert "$RHBK_CA_FILE" -fsS \
  -H "Authorization: Bearer ${RHBK_ADMIN_TOKEN}" \
  "https://${RHBK_HOST}/admin/realms/rhoai/groups?search=rhoai-week7-users&exact=true" | \
  jq -er '.[0].id')"

test "$(curl --cacert "$RHBK_CA_FILE" -sS -o /dev/null -w '%{http_code}' \
  -X PUT \
  -H "Authorization: Bearer ${RHBK_ADMIN_TOKEN}" \
  "https://${RHBK_HOST}/admin/realms/rhoai/users/${EXTERNAL_USER_ID}/groups/${EXTERNAL_GROUP_ID}")" = 204
```

### 검증용 모델과 group policy 생성

모델 목록과 group mapping만 확인하기 위해 외부 호출을 하지 않는 metadata용 `ExternalModel`을 사용한다. 이 모델 endpoint로 inference 요청은 보내지 않는다.

```bash
oc create secret generic week7-external-model-credential \
  -n week7-rhcl-authz \
  --from-literal=api-key=not-used-for-model-list-validation

oc apply -f - <<'EOF'
apiVersion: maas.opendatahub.io/v1alpha1
kind: ExternalModel
metadata:
  name: week7-oidc-model
  namespace: week7-rhcl-authz
spec:
  provider: openai
  endpoint: api.openai.com
  targetModel: gpt-4o-mini
  credentialRef:
    name: week7-external-model-credential
---
apiVersion: maas.opendatahub.io/v1alpha1
kind: MaaSModelRef
metadata:
  name: week7-oidc-model
  namespace: week7-rhcl-authz
spec:
  modelRef:
    kind: ExternalModel
    name: week7-oidc-model
EOF

for i in $(seq 1 60); do
  MODEL_PHASE="$(oc get maasmodelref week7-oidc-model \
    -n week7-rhcl-authz -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  test "$MODEL_PHASE" = Ready && break
  sleep 2
done
test "$MODEL_PHASE" = Ready
```

```bash
oc apply -f - <<'EOF'
apiVersion: maas.opendatahub.io/v1alpha1
kind: MaaSSubscription
metadata:
  name: week7-oidc-users
  namespace: models-as-a-service
spec:
  owner:
    groups:
      - name: rhoai-week7-users
    users: []
  modelRefs:
    - name: week7-oidc-model
      namespace: week7-rhcl-authz
      tokenRateLimits:
        - limit: 1000
          window: 1h
  priority: 100
---
apiVersion: maas.opendatahub.io/v1alpha1
kind: MaaSAuthPolicy
metadata:
  name: week7-oidc-users
  namespace: models-as-a-service
spec:
  subjects:
    groups:
      - name: rhoai-week7-users
    users: []
  modelRefs:
    - name: week7-oidc-model
      namespace: week7-rhcl-authz
EOF

for i in $(seq 1 60); do
  SUB_PHASE="$(oc get maassubscription week7-oidc-users \
    -n models-as-a-service -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  POLICY_PHASE="$(oc get maasauthpolicy week7-oidc-users \
    -n models-as-a-service -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  test "${SUB_PHASE}/${POLICY_PHASE}" = 'Active/Active' && break
  sleep 2
done
test "${SUB_PHASE}/${POLICY_PHASE}" = 'Active/Active'
```

### 외부 OIDC 사용자와 비허용 그룹 비교

```bash
EXTERNAL_TOKEN="$(get_rhbk_token \
  "$EXTERNAL_USERNAME" "$EXTERNAL_PASSWORD")"

if oc get user "$EXTERNAL_USERNAME" >/dev/null 2>&1; then
  echo 'Unexpected OpenShift User object exists' >&2
  exit 1
else
  echo 'OpenShift User object: not found (expected)'
fi

curl -sk \
  -H "Authorization: Bearer ${EXTERNAL_TOKEN}" \
  https://maas.apps.sno.ocp422.com/maas-api/v1/models \
  > /tmp/week7-external-models.json

jq '{count:(.data|length),ids:[.data[].id]}' \
  /tmp/week7-external-models.json
jq -e '.data | length == 1 and .[0].id == "week7-oidc-model"' \
  /tmp/week7-external-models.json

curl -sk \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  https://maas.apps.sno.ocp422.com/maas-api/v1/models \
  > /tmp/week7-admin-models.json

jq '{count:(.data|length),ids:[.data[].id]}' \
  /tmp/week7-admin-models.json
jq -e '.data | length == 0' /tmp/week7-admin-models.json

rm -f /tmp/week7-external-models.json /tmp/week7-admin-models.json
```

허용 사용자는 HTTP `200`과 모델 1개를 받고, 다른 group의 admin도 인증 자체는 `200`이지만 조회 가능한 모델은 0개다. 이는 필수 GA 예제의 route-level `403`과 MaaS 모델 목록 필터링의 차이다.

### 원복

SSH를 다시 접속했다면 백업 경로부터 복구한다.

```bash
printf 'Current WEEK7_STEP2_BACKUP_DIR=%s\n' \
  "${WEEK7_STEP2_BACKUP_DIR:-<unset>}"
cat /tmp/week7-step2-active-backup 2>/dev/null || true
ls -ld /tmp/week7-step2-before-* 2>/dev/null || true

if test -z "${WEEK7_STEP2_BACKUP_DIR:-}"; then
  WEEK7_STEP2_BACKUP_DIR="$(cat /tmp/week7-step2-active-backup)"
  export WEEK7_STEP2_BACKUP_DIR
fi

test -s "$WEEK7_STEP2_BACKUP_DIR/authorino.json"
test -s "$WEEK7_STEP2_BACKUP_DIR/tenant.json"
printf 'Using WEEK7_STEP2_BACKUP_DIR=%s\n' "$WEEK7_STEP2_BACKUP_DIR"
```

선택 TP를 수행했다면 policy와 subscription을 먼저 제거하고 Tenant를 원래 값으로 되돌린다.

```bash
oc delete maasauthpolicy week7-oidc-users \
  -n models-as-a-service --ignore-not-found --wait=true
oc delete maassubscription week7-oidc-users \
  -n models-as-a-service --ignore-not-found --wait=true

ORIGINAL_EXTERNAL_OIDC="$(jq -c '.spec.externalOIDC // null' \
  "$WEEK7_STEP2_BACKUP_DIR/tenant.json")"
oc patch tenant default-tenant -n models-as-a-service \
  --type=merge -p "$(jq -n --argjson oidc "$ORIGINAL_EXTERNAL_OIDC" \
  '{spec:{externalOIDC:$oidc}}')"
unset ORIGINAL_EXTERNAL_OIDC
```

Step2 전용 RHBK 사용자가 남아 있으면 삭제한다. shell 변수가 사라졌을 수 있으므로 관리자 token을 다시 얻는다.

```bash
APPS_DOMAIN="$(oc get ingress.config cluster -o jsonpath='{.spec.domain}')"
RHBK_HOST="week7-rhbk.${APPS_DOMAIN}"
RHBK_CA_FILE="$(mktemp)"
chmod 600 "$RHBK_CA_FILE"
oc get secret week7-rhbk-tls -n week7-rhbk \
  -o jsonpath='{.data.ca\.crt}' | base64 -d > "$RHBK_CA_FILE"

RHBK_ADMIN_USER="$(oc get secret week7-rhbk-initial-admin \
  -n week7-rhbk -o jsonpath='{.data.username}' | base64 -d)"
RHBK_ADMIN_PASSWORD="$(oc get secret week7-rhbk-initial-admin \
  -n week7-rhbk -o jsonpath='{.data.password}' | base64 -d)"
RHBK_ADMIN_TOKEN="$(curl --cacert "$RHBK_CA_FILE" -fsS \
  -d grant_type=password -d client_id=admin-cli \
  --data-urlencode username="$RHBK_ADMIN_USER" \
  --data-urlencode password="$RHBK_ADMIN_PASSWORD" \
  "https://${RHBK_HOST}/realms/master/protocol/openid-connect/token" | \
  jq -er '.access_token')"

EXTERNAL_USER_ID="$(curl --cacert "$RHBK_CA_FILE" -fsS \
  -H "Authorization: Bearer ${RHBK_ADMIN_TOKEN}" \
  "https://${RHBK_HOST}/admin/realms/rhoai/users?username=rhoai-week7-external&exact=true" | \
  jq -r '.[0].id // empty')"

if test -n "$EXTERNAL_USER_ID"; then
  curl --cacert "$RHBK_CA_FILE" -fsS -X DELETE \
    -H "Authorization: Bearer ${RHBK_ADMIN_TOKEN}" \
    "https://${RHBK_HOST}/admin/realms/rhoai/users/${EXTERNAL_USER_ID}"
fi
```

GA/TP 리소스를 담은 Namespace를 삭제하고 Authorino volume을 백업 값으로 복원한다. Authorino CR 자체를 `replace --force`로 삭제하지 않는다.

```bash
oc delete namespace week7-rhcl-authz \
  --ignore-not-found --wait=true

ORIGINAL_VOLUMES="$(jq -c '.spec.volumes // null' \
  "$WEEK7_STEP2_BACKUP_DIR/authorino.json")"
oc patch authorino authorino -n kuadrant-system \
  --type=merge -p "$(jq -n --argjson volumes "$ORIGINAL_VOLUMES" \
  '{spec:{volumes:$volumes}}')"

oc rollout status deployment/authorino \
  -n kuadrant-system --timeout=300s
oc delete configmap authorino-week7-ca \
  -n kuadrant-system --ignore-not-found

rm -f "$RHBK_CA_FILE" /tmp/week7-step2-active-backup
rm -rf "$WEEK7_STEP2_BACKUP_DIR"

unset WEEK7_STEP2_BACKUP_DIR RHBK_CA_FILE
unset APPS_DOMAIN RHBK_HOST RHBK_ISSUER RHCL_HOST GW_SERVICE ECHO_IMAGE
unset PRE_POLICY_BODY NO_TOKEN_CODE USER_CODE ADMIN_CODE
unset CLIENT_SECRET ADMIN_PASSWORD USER_PASSWORD USER_TOKEN ADMIN_TOKEN
unset RHBK_ADMIN_USER RHBK_ADMIN_PASSWORD RHBK_ADMIN_TOKEN
unset EXTERNAL_USERNAME EXTERNAL_PASSWORD EXTERNAL_USER_ID EXTERNAL_GROUP_ID
unset EXTERNAL_TOKEN EXISTING_ID USER_JSON
```

마지막 상태를 확인한다.

```bash
oc get tenant default-tenant -n models-as-a-service -o json | jq '{
  externalOIDC: (.spec.externalOIDC // null),
  ready: (.status.conditions[] | select(.type == "Ready") | .status)
}'
oc get authpolicy maas-api-auth-policy \
  -n redhat-ods-applications -o json | \
  jq '.spec.rules.authentication | keys'
curl -skf https://maas.apps.sno.ocp422.com/maas-api/health | jq .
oc get namespace week7-rhcl-authz
```

기본 상태에서는 `externalOIDC=null`, Tenant Ready, MaaS health `healthy`다. 마지막 Namespace 조회의 `NotFound`는 정상이다. RHBK를 더 사용하지 않을 때만 [Week7 Step 1 원복](<Week7-Step1 RHBK OIDC 실습.md#원복>)을 실행한다.

### 장애 진단

- token이 모두 `401`: Authorino Pod에서 issuer discovery를 실행해 RHBK CA와 issuer를 확인한다.
- 두 group이 모두 `200`: live `AuthPolicy`와 생성된 `AuthConfig`에 inline `selector/operator/value`가 남아 있는지 확인한다.
- `503 wasm_fail_stream`: Gateway Pod의 Kuadrant WASM 다운로드 상태를 확인한다. `fetch_failures`만 있고 success가 없으면 Kuadrant WASM Service 준비 후 Gateway를 재시작한다.

```bash
MAAS_GATEWAY_POD="$(oc get pod -n openshift-ingress \
  -l gateway.networking.k8s.io/gateway-name=maas-default-gateway \
  -o jsonpath='{.items[0].metadata.name}')"
oc exec -n openshift-ingress "$MAAS_GATEWAY_POD" -- \
  pilot-agent request GET 'stats?filter=wasm.remote_load'

oc rollout restart \
  deployment/maas-default-gateway-data-science-gateway-class \
  -n openshift-ingress
oc rollout status \
  deployment/maas-default-gateway-data-science-gateway-class \
  -n openshift-ingress --timeout=300s
```

### 공식 문서

- [RHCL 1.4 - Using OpenID Connect authentication](https://docs.redhat.com/en/documentation/red_hat_connectivity_link/1.4/html/deploying_red_hat_connectivity_link/rhcl-oidc-authentication)
- [RHCL 1.4 - Installing in a disconnected environment](https://docs.redhat.com/en/documentation/red_hat_connectivity_link/1.4/html/installing_connectivity_link/rhcl-install-disconnected)
- [RHOAI 3.4 - Configure external OIDC authentication for MaaS](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/govern_llm_access_with_models-as-a-service/deploy-and-manage-models-as-a-service_maas#configure-external-oidc-authentication-for-models-as-a-service_deploy-and-manage-models-as-a-service)
- [RHBK 26.6 - Securing applications with OIDC](https://docs.redhat.com/en/documentation/red_hat_build_of_keycloak/26.6/html/securing_applications_and_services_guide/oidc-layers-)
