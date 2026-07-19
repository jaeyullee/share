# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 7 - Step 1 RHBK 기반 엔터프라이즈 OIDC

> 사전 준비: [Week7 Step0](<Week7-Step0 사전점검 실습.md>)을 수행하고 `rhbk-operator`가 폐쇄망 CatalogSource에서 조회되는지 확인한다. 인증 변경 중에도 사용할 수 있는 인증서 기반 `kubeconfig`를 별도 셸에 유지한다.

Red Hat build of Keycloak(RHBK)에 `rhoai` realm, OpenShift OAuth client, 사용자와 그룹을 선언하고 OpenShift OAuth의 OpenID identity provider로 연결한다. 기존 `htpasswd` IdP는 제거하지 않는다.

```text
RHBK user/group
  -> OIDC token groups claim
  -> OpenShift User/Identity/Group
  -> RHOAI ClusterRoleBinding과 프로젝트 RBAC
```

### RHBK Operator 설치

```bash
oc get packagemanifest rhbk-operator -n openshift-marketplace \
  -o json | jq '{
    source: .status.catalogSource,
    defaultChannel: .status.defaultChannel,
    csv: [.status.channels[] | select(.name == "stable-v26.6") | .currentCSV]
  }'
```

`stable-v26.6`과 `rhbk-operator.v26.6.4-opr.1`을 확인한 다음 설치한다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: week7-rhbk
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: rhbk-operator
  namespace: week7-rhbk
spec:
  targetNamespaces:
    - week7-rhbk
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: rhbk-operator
  namespace: week7-rhbk
spec:
  channel: stable-v26.6
  installPlanApproval: Automatic
  name: rhbk-operator
  source: cs-rhbk-operator-index-v4-22
  sourceNamespace: openshift-marketplace
EOF

oc get subscription,csv,pod -n week7-rhbk -w
```

RHBK 26.6 Operator는 `OwnNamespace`와 `SingleNamespace` 설치만 지원한다. 따라서 Operator와 `Keycloak` CR을 같은 `week7-rhbk` Namespace에 둔다. CSV가 `Succeeded`이고 Operator Pod가 `Running`이면 감시를 종료한다.

### 실습용 PostgreSQL과 TLS 준비

RHBK Operator는 DB를 생성하지 않는다. 이 실습에서는 단일 PostgreSQL과 self-signed 인증서를 사용한다. 운영에서는 외부 관리형 PostgreSQL, 조직 CA, DB TLS와 백업 정책을 별도로 설계한다.

```bash
RHBK_DB_PASSWORD="$(openssl rand -hex 24)"
oc create secret generic week7-rhbk-db -n week7-rhbk \
  --from-literal=database-user=rhbk \
  --from-literal=database-password="$RHBK_DB_PASSWORD" \
  --from-literal=database-name=keycloak \
  --from-literal=username=rhbk \
  --from-literal=password="$RHBK_DB_PASSWORD"
unset RHBK_DB_PASSWORD

APPS_DOMAIN="$(oc get ingress.config.openshift.io cluster \
  -o jsonpath='{.spec.domain}')"
RHBK_HOST="week7-rhbk.${APPS_DOMAIN}"
printf 'RHBK_HOST=%s\n' "$RHBK_HOST"
```

```bash
oc apply -f - <<'EOF'
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: week7-selfsigned
  namespace: week7-rhbk
spec:
  selfSigned: {}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: week7-rhbk-db
  namespace: week7-rhbk
spec:
  storageClassName: truenas-nfs
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: week7-rhbk-db
  namespace: week7-rhbk
spec:
  replicas: 1
  selector:
    matchLabels:
      app: week7-rhbk-db
  template:
    metadata:
      labels:
        app: week7-rhbk-db
    spec:
      containers:
        - name: postgresql
          image: registry.redhat.io/rhel9/postgresql-16@sha256:d5842e96059ffa6020c22525014455637990543ffb126768d27b057cff2bb40a
          env:
            - name: POSTGRESQL_USER
              valueFrom:
                secretKeyRef:
                  name: week7-rhbk-db
                  key: database-user
            - name: POSTGRESQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: week7-rhbk-db
                  key: database-password
            - name: POSTGRESQL_DATABASE
              valueFrom:
                secretKeyRef:
                  name: week7-rhbk-db
                  key: database-name
          ports:
            - name: postgresql
              containerPort: 5432
          resources:
            requests:
              cpu: 100m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
          volumeMounts:
            - name: data
              mountPath: /var/lib/pgsql/data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: week7-rhbk-db
---
apiVersion: v1
kind: Service
metadata:
  name: week7-rhbk-db
  namespace: week7-rhbk
spec:
  selector:
    app: week7-rhbk-db
  ports:
    - name: postgresql
      port: 5432
      targetPort: postgresql
EOF

sed "s/__RHBK_HOST__/${RHBK_HOST}/g" <<'EOF' | oc apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: week7-rhbk
  namespace: week7-rhbk
spec:
  secretName: week7-rhbk-tls
  commonName: __RHBK_HOST__
  dnsNames:
    - __RHBK_HOST__
  issuerRef:
    name: week7-selfsigned
    kind: Issuer
EOF

oc rollout status deployment/week7-rhbk-db \
  -n week7-rhbk --timeout=300s
oc wait certificate/week7-rhbk -n week7-rhbk \
  --for=condition=Ready --timeout=120s
```

### Keycloak 인스턴스 생성

```bash
sed "s/__RHBK_HOST__/${RHBK_HOST}/g" <<'EOF' | oc apply -f -
apiVersion: k8s.keycloak.org/v2beta1
kind: Keycloak
metadata:
  name: week7-rhbk
  namespace: week7-rhbk
spec:
  instances: 1
  db:
    vendor: postgres
    host: week7-rhbk-db
    port: 5432
    database: keycloak
    usernameSecret:
      name: week7-rhbk-db
      key: username
    passwordSecret:
      name: week7-rhbk-db
      key: password
  http:
    tlsSecret: week7-rhbk-tls
  hostname:
    hostname: __RHBK_HOST__
  ingress:
    className: openshift-default
  proxy:
    headers: xforwarded
  resources:
    requests:
      cpu: 250m
      memory: 1Gi
    limits:
      cpu: "1"
      memory: 2Gi
EOF

oc get keycloak week7-rhbk -n week7-rhbk -w
```

`Ready=True`, `HasErrors=False`가 되면 다음을 확인한다.

```bash
oc get keycloak week7-rhbk -n week7-rhbk -o yaml | \
  sed -n '/status:/,$p'
oc get deployment,pod,service,ingress,route -n week7-rhbk
```

### Realm, client, group, user 선언

RHOAI 관리자 그룹은 현재 기본 ClusterRoleBinding이 사용하는 `rhods-admins`로 만들고, 일반 사용자 그룹은 `rhoai-week7-users`로 만든다. 비밀번호와 OAuth client secret은 `KeycloakRealmImport`의 Secret placeholder로 주입한다.

```bash
read -rsp 'RHBK admin test user password: ' RHBK_ADMIN_PASSWORD
echo
read -rsp 'RHBK regular test user password: ' RHBK_USER_PASSWORD
echo
RHBK_CLIENT_SECRET="$(openssl rand -hex 32)"

oc create secret generic week7-rhbk-realm-secrets -n week7-rhbk \
  --from-literal=CLIENT_SECRET="$RHBK_CLIENT_SECRET" \
  --from-literal=ADMIN_PASSWORD="$RHBK_ADMIN_PASSWORD" \
  --from-literal=USER_PASSWORD="$RHBK_USER_PASSWORD"

unset RHBK_CLIENT_SECRET RHBK_ADMIN_PASSWORD RHBK_USER_PASSWORD

OAUTH_REDIRECT="https://oauth-openshift.${APPS_DOMAIN}/oauth2callback/week7-rhbk"
sed "s|__OAUTH_REDIRECT__|${OAUTH_REDIRECT}|g" <<'EOF' | oc apply -f -
apiVersion: k8s.keycloak.org/v2beta1
kind: KeycloakRealmImport
metadata:
  name: week7-rhoai-realm
  namespace: week7-rhbk
spec:
  keycloakCRName: week7-rhbk
  placeholders:
    CLIENT_SECRET:
      secret:
        name: week7-rhbk-realm-secrets
        key: CLIENT_SECRET
    ADMIN_PASSWORD:
      secret:
        name: week7-rhbk-realm-secrets
        key: ADMIN_PASSWORD
    USER_PASSWORD:
      secret:
        name: week7-rhbk-realm-secrets
        key: USER_PASSWORD
  realm:
    id: rhoai
    realm: rhoai
    displayName: RHOAI Week7
    enabled: true
    sslRequired: external
    loginWithEmailAllowed: true
    registrationAllowed: false
    groups:
      - name: rhods-admins
      - name: rhoai-week7-users
    users:
      - username: rhoai-week7-admin
        enabled: true
        firstName: RHOAI
        lastName: Administrator
        email: rhoai-week7-admin@example.invalid
        emailVerified: true
        groups:
          - /rhods-admins
        credentials:
          - type: password
            value: "${ADMIN_PASSWORD}"
            temporary: false
      - username: rhoai-week7-user
        enabled: true
        firstName: RHOAI
        lastName: User
        email: rhoai-week7-user@example.invalid
        emailVerified: true
        groups:
          - /rhoai-week7-users
        credentials:
          - type: password
            value: "${USER_PASSWORD}"
            temporary: false
    clients:
      - clientId: openshift
        name: OpenShift OAuth
        enabled: true
        protocol: openid-connect
        publicClient: false
        secret: "${CLIENT_SECRET}"
        standardFlowEnabled: true
        directAccessGrantsEnabled: true
        redirectUris:
          - __OAUTH_REDIRECT__
        webOrigins:
          - "+"
        protocolMappers:
          - name: groups
            protocol: openid-connect
            protocolMapper: oidc-group-membership-mapper
            config:
              claim.name: groups
              full.path: "false"
              id.token.claim: "true"
              access.token.claim: "true"
              userinfo.token.claim: "true"
              jsonType.label: String
EOF

oc get keycloakrealmimport week7-rhoai-realm \
  -n week7-rhbk -w
```

`Done=True`, `HasErrors=False`가 되면 import CR을 삭제해 완료된 Job과 Pod를 정리한다. realm 데이터는 PostgreSQL에 유지된다.

```bash
oc delete keycloakrealmimport week7-rhoai-realm -n week7-rhbk
```

### OpenShift OAuth에 RHBK 추가

```bash
printf 'Current WEEK7_BACKUP_DIR=%s\n' "${WEEK7_BACKUP_DIR:-<unset>}"
ls -ld /tmp/week7-before-* 2>/dev/null || true
read -r -p '위 목록에서 사용할 Week7 백업 디렉터리 전체 경로: ' WEEK7_BACKUP_DIR
export WEEK7_BACKUP_DIR
test -s "$WEEK7_BACKUP_DIR/oauth.json"
test -s "$WEEK7_BACKUP_DIR/console.json"
printf 'Using WEEK7_BACKUP_DIR=%s\n' "$WEEK7_BACKUP_DIR"

TLS_FILE="$(mktemp)"
CLIENT_FILE="$(mktemp)"
chmod 600 "$TLS_FILE" "$CLIENT_FILE"

oc get secret week7-rhbk-tls -n week7-rhbk \
  -o jsonpath='{.data.tls\.crt}' | base64 -d > "$TLS_FILE"
oc get secret week7-rhbk-realm-secrets -n week7-rhbk \
  -o jsonpath='{.data.CLIENT_SECRET}' | base64 -d > "$CLIENT_FILE"

oc create configmap week7-rhbk-ca -n openshift-config \
  --from-file=ca.crt="$TLS_FILE"
oc create secret generic week7-rhbk-oidc -n openshift-config \
  --from-file=clientSecret="$CLIENT_FILE"

rm -f "$TLS_FILE" "$CLIENT_FILE"

RHBK_ISSUER="https://${RHBK_HOST}/realms/rhoai"
IDP_JSON="$(jq -n --arg issuer "$RHBK_ISSUER" '{
  name: "week7-rhbk",
  mappingMethod: "claim",
  type: "OpenID",
  openID: {
    clientID: "openshift",
    clientSecret: {name: "week7-rhbk-oidc"},
    ca: {name: "week7-rhbk-ca"},
    issuer: $issuer,
    claims: {
      preferredUsername: ["preferred_username", "email"],
      name: ["name"],
      email: ["email"],
      groups: ["groups"]
    }
  }
}')"

CURRENT_IDPS="$(oc get oauth cluster -o json | \
  jq --arg name week7-rhbk --argjson idp "$IDP_JSON" \
  '(.spec.identityProviders // []) | map(select(.name != $name)) + [$idp]')"

oc patch oauth cluster --type=merge \
  -p "$(jq -n --argjson idps "$CURRENT_IDPS" \
  '{spec:{identityProviders:$idps}}')"

unset IDP_JSON CURRENT_IDPS
oc wait clusteroperator/authentication \
  --for=condition=Available=True --timeout=300s
oc get clusteroperator authentication
```

`htpasswd`와 `week7-rhbk`가 함께 있어야 한다.

```bash
oc get oauth cluster -o json | \
  jq -r '.spec.identityProviders[] | [.name, .type] | @tsv'
```

OpenShift Console 로그아웃 뒤에도 RHBK 브라우저 세션이 남아 자동으로 다시 로그인되는 것을 막기 위해 Console의 로그아웃 후 이동 경로를 RHBK logout endpoint로 설정한다.

```bash
RHBK_LOGOUT_URL="${RHBK_ISSUER}/protocol/openid-connect/logout"

oc patch console.config.openshift.io cluster --type=merge \
  -p "$(jq -n --arg url "$RHBK_LOGOUT_URL" \
  '{spec:{authentication:{logoutRedirect:$url}}}')"

oc wait clusteroperator/console \
  --for=condition=Available=True --timeout=300s
oc get console.config.openshift.io cluster \
  -o jsonpath='{.spec.authentication.logoutRedirect}{"\n"}'
```

출력은 RHBK realm의 `/protocol/openid-connect/logout` URL이어야 한다. 로그아웃 시 RHBK의 `Logging out` 확인 화면이 나타나면 로그아웃을 완료한 뒤 다음 계정으로 로그인한다.

### issuer와 group claim 검증

```bash
CA_FILE="$(mktemp)"
chmod 600 "$CA_FILE"
oc get configmap week7-rhbk-ca -n openshift-config \
  -o jsonpath='{.data.ca\.crt}' > "$CA_FILE"

curl --cacert "$CA_FILE" -fsS \
  "${RHBK_ISSUER}/.well-known/openid-configuration" | \
  jq '{issuer,authorization_endpoint,token_endpoint}'
```

RHBK 사용자의 비밀번호를 다시 입력해 직접 token의 group claim을 확인한다. 이 검증은 RHBK realm과 mapper 확인이며, 실제 OpenShift 로그인은 다음 브라우저 절차로 확인한다.

```bash
read -rsp 'RHBK admin test user password: ' RHBK_ADMIN_PASSWORD
echo
CLIENT_SECRET="$(oc get secret week7-rhbk-realm-secrets \
  -n week7-rhbk -o jsonpath='{.data.CLIENT_SECRET}' | base64 -d)"

ACCESS_TOKEN="$(curl --cacert "$CA_FILE" -fsS \
  -d grant_type=password \
  -d client_id=openshift \
  --data-urlencode client_secret="$CLIENT_SECRET" \
  --data-urlencode username=rhoai-week7-admin \
  --data-urlencode password="$RHBK_ADMIN_PASSWORD" \
  "${RHBK_ISSUER}/protocol/openid-connect/token" | \
  jq -r '.access_token')"

python3 - "$ACCESS_TOKEN" <<'PY'
import base64
import json
import sys

payload = sys.argv[1].split('.')[1]
payload += '=' * (-len(payload) % 4)
claims = json.loads(base64.urlsafe_b64decode(payload))
print(json.dumps({
    'preferred_username': claims.get('preferred_username'),
    'groups': claims.get('groups'),
}, ensure_ascii=False, indent=2))
PY

unset ACCESS_TOKEN CLIENT_SECRET RHBK_ADMIN_PASSWORD
rm -f "$CA_FILE"
```

예상 group은 `rhods-admins`다.

1. 시크릿 브라우저에서 OpenShift Console을 연다.
2. 로그인 옵션에서 `week7-rhbk`를 선택한다.
3. `rhoai-week7-admin`으로 로그인한다.
4. RHOAI Dashboard의 Settings에 접근되는지 확인한다.
5. 로그아웃하고 RHBK 로그아웃 확인 화면을 완료한 뒤 `rhoai-week7-user`로 로그인한다.
6. 일반 프로젝트 기능은 보이지만 관리자 Settings 변경 권한은 없는지 확인한다.

로그인 후 OpenShift가 token의 group claim을 동기화했는지 인증서 기반 관리자 셸에서 확인한다.

```bash
oc get user rhoai-week7-admin rhoai-week7-user
oc get group rhods-admins rhoai-week7-users -o yaml

oc auth can-i update odhdashboardconfigs.opendatahub.io \
  -n redhat-ods-applications \
  --as=rhoai-week7-admin --as-group=rhods-admins

oc auth can-i update odhdashboardconfigs.opendatahub.io \
  -n redhat-ods-applications \
  --as=rhoai-week7-user --as-group=rhoai-week7-users
```

관리자는 `yes`, 일반 사용자는 `no`여야 한다. `get`은 인증된 일반 사용자에게도 허용될 수 있으므로 관리자 권한 구분 기준으로 사용하지 않는다.

### 원복

> [Week7 Step 2](<Week7-Step2 RHCL OIDC 인가 실습.md>)를 계속 진행한다면 이 절을 실행하지 않는다. Step2는 이 RHBK issuer, client, user/group과 CA를 그대로 사용한다. Step2를 완료하고 RHBK가 더 필요하지 않을 때 이 절로 돌아온다.

먼저 OpenShift OAuth에서 실습 IdP를 제거한 뒤 RHBK를 삭제한다.

```bash
printf 'Current WEEK7_BACKUP_DIR=%s\n' "${WEEK7_BACKUP_DIR:-<unset>}"
ls -ld /tmp/week7-before-* 2>/dev/null || true
read -r -p '위 목록에서 사용할 Week7 백업 디렉터리 전체 경로: ' WEEK7_BACKUP_DIR
export WEEK7_BACKUP_DIR
test -s "$WEEK7_BACKUP_DIR/oauth.json"
test -s "$WEEK7_BACKUP_DIR/console.json"
printf 'Using WEEK7_BACKUP_DIR=%s\n' "$WEEK7_BACKUP_DIR"

ORIGINAL_IDPS="$(jq -c '.spec.identityProviders // []' \
  "$WEEK7_BACKUP_DIR/oauth.json")"
oc patch oauth cluster --type=merge \
  -p "$(jq -n --argjson idps "$ORIGINAL_IDPS" \
  '{spec:{identityProviders:$idps}}')"
unset ORIGINAL_IDPS

ORIGINAL_CONSOLE_PATCH="$(jq -c '
  if .spec.authentication == null then
    {spec:{authentication:null}}
  else
    {spec:{authentication:.spec.authentication}}
  end' "$WEEK7_BACKUP_DIR/console.json")"
oc patch console.config.openshift.io cluster --type=merge \
  -p "$ORIGINAL_CONSOLE_PATCH"
unset ORIGINAL_CONSOLE_PATCH

oc delete secret/week7-rhbk-oidc \
  configmap/week7-rhbk-ca -n openshift-config --ignore-not-found
oc wait clusteroperator/authentication \
  --for=condition=Available=True --timeout=300s
oc wait clusteroperator/console \
  --for=condition=Available=True --timeout=300s

oc adm groups remove-users rhods-admins rhoai-week7-admin || true
oc delete group rhoai-week7-users --ignore-not-found

oc get oauthaccesstoken -o json | \
  jq -r '.items[] | select(.userName | startswith("rhoai-week7-")) | .metadata.name' | \
  xargs -r oc delete oauthaccesstoken
oc get oauthauthorizetoken -o json | \
  jq -r '.items[] | select(.userName | startswith("rhoai-week7-")) | .metadata.name' | \
  xargs -r oc delete oauthauthorizetoken

oc delete user rhoai-week7-admin rhoai-week7-user --ignore-not-found
oc get identity -o name | grep '^identity.user.openshift.io/week7-rhbk:' | \
  xargs -r oc delete

oc delete keycloak week7-rhbk -n week7-rhbk --wait=true \
  --ignore-not-found
oc delete namespace week7-rhbk --wait=true
oc delete crd keycloaks.k8s.keycloak.org \
  keycloakrealmimports.k8s.keycloak.org --ignore-not-found
unset RHBK_HOST RHBK_ISSUER RHBK_LOGOUT_URL APPS_DOMAIN OAUTH_REDIRECT
```

Namespace를 삭제하면 그 안의 Subscription, CSV와 Operator도 함께 제거된다. 미러 image, CatalogSource와 IDMS는 재설치 선행조건이므로 유지한다. 마지막으로 OAuth IdP 목록에 기존 `htpasswd`만 남았고 `week7-rhbk` Namespace/User/Identity가 없는지 확인한다.

### 공식 문서

- [RHBK 26.6 - Operator installation and basic deployment](https://docs.redhat.com/en/documentation/red_hat_build_of_keycloak/26.6/html/operator_guide/basic-deployment-)
- [RHBK 26.6 - Automating a realm import](https://docs.redhat.com/en/documentation/red_hat_build_of_keycloak/26.6/html-single/operator_guide/index)
- [OpenShift 4.22 - Configuring an OpenID identity provider](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/authentication_and_authorization/configuring-identity-providers)
- [RHOAI 3.4 - Managing users and groups](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/managing_openshift_ai/managing-users-and-groups)
