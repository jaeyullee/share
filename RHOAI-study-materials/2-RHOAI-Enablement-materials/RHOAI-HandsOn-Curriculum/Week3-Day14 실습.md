# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 3 - Day14

LLM을 OpenAI 호환 API로 서빙하고 RHOAI Models-as-a-Service의 subscription, authorization, API key, token quota를 확인한다.

### 기능 범위
- RHOAI 3.4의 Models-as-a-Service 자체는 GA다.
- MaaS의 subscription, authorization policy, self-service API key는 GA다.
- vLLM runtime을 MaaS에 직접 연결하는 기능은 TP다.
- MaaS observability dashboard와 외부 model egress도 TP다.
- 기본 실습은 `LLMInferenceService`와 MaaS GA 기능을 사용하고, vLLM RawDeployment는 비교 단계로 둔다.

### 사전 조건 확인
```bash
oc get dsc default-dsc
oc get node ocp-w01-gpu \
  -o jsonpath='{.status.allocatable.nvidia\.com/gpu}{"\n"}'
oc get crd llminferenceservices.serving.kserve.io
oc get subscription -A | grep -E 'leader-worker-set|rhcl-operator'
oc get configmap cluster-monitoring-config -n openshift-monitoring \
  -o jsonpath='{.data.config\.yaml}'
```

Day13의 User Workload Monitoring, Day11의 GPU, Leader Worker Set Operator가 준비되어 있어야 한다.

> `oc debug node/ocp-w01-gpu -- chroot /host lspci -nn | grep -i nvidia`가 비어 있으면 LLM 배포 단계는 진행할 수 없다. MaaS 컨트롤 플레인과 정책 CR 검증은 가능하지만 실제 GPU 추론 검증은 PCI passthrough 복구 후 수행한다.

### Red Hat Connectivity Link Operator 설치
RHCL은 MaaS의 Gateway, Authorino, Limitador, Kuadrant policy 계층을 제공한다.

> RHCL 1.4.1은 `dns-operator 1.4.0`, `authorino-operator 1.4.1`, `limitador-operator 1.4.0`을 OLM 의존성으로 설치한다. 폐쇄망 카탈로그에 네 패키지와 operand 이미지가 모두 있어야 한다.

```bash
oc apply -f - <<'EOF'
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: rhcl-operator
  namespace: openshift-operators
spec:
  channel: stable
  installPlanApproval: Automatic
  name: rhcl-operator
  source: cs-redhat-operator-index-v4-22
  sourceNamespace: openshift-marketplace
EOF

oc get csv,subscription -n openshift-operators | grep -Ei 'rhcl|connectivity'
oc get pods -n openshift-operators | grep -Ei 'rhcl|kuadrant'
```

### Kuadrant 인스턴스 생성
현재 CSV가 제공하는 CR 예제의 apiVersion을 먼저 확인한다.

```bash
RHCL_CSV=$(oc get csv -n openshift-operators \
  -o jsonpath='{.items[?(@.spec.displayName=="Red Hat Connectivity Link")].metadata.name}')
oc get csv "$RHCL_CSV" -n openshift-operators \
  -o jsonpath='{.metadata.annotations.alm-examples}' | jq .
```

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: kuadrant-system
---
apiVersion: kuadrant.io/v1beta1
kind: Kuadrant
metadata:
  name: kuadrant
  namespace: kuadrant-system
spec: {}
EOF

oc get kuadrant kuadrant -n kuadrant-system -w
oc get pods -n kuadrant-system
```

이 홈랩의 `data-science-gateway-class`는 OpenShift CIO가 관리하는 Istio GatewayClass다. OCP 4.19 이상에서 이 토폴로지는 Kuadrant mTLS에 필요한 service-mesh sidecar 경로를 제공하지 않으므로 mTLS를 활성화하지 않는다. 활성화하면 Gateway에서 Authorino/Limitador로 가는 ext-auth gRPC가 `500`으로 실패한다.

```bash
oc patch kuadrant kuadrant -n kuadrant-system --type=merge \
  -p '{"spec":{"mtls":null}}'
oc get kuadrant kuadrant -n kuadrant-system
```

API key 인증 시 Authorino가 MaaS 내부 HTTPS endpoint의 OpenShift service CA를 신뢰하도록 CA를 mount한다. 이 설정이 없으면 OpenShift token 요청은 통과해도 MaaS API key 검증은 `403`으로 실패한다.

```bash
oc get configmap openshift-service-ca.crt -n kuadrant-system \
  -o jsonpath='{.data.service-ca\.crt}' > /tmp/service-ca.crt

oc create configmap authorino-openshift-service-ca \
  -n kuadrant-system \
  --from-file=service-ca.crt=/tmp/service-ca.crt \
  --dry-run=client -o yaml | oc apply -f -

oc patch authorino authorino -n kuadrant-system --type=merge -p '
{"spec":{"volumes":{"items":[{"name":"openshift-service-ca","mountPath":"/etc/ssl/certs","configMaps":["authorino-openshift-service-ca"],"items":[{"key":"service-ca.crt","path":"service-ca.crt"}]}],"defaultMode":420}}}'

oc rollout status deployment/authorino -n kuadrant-system --timeout=300s
rm -f /tmp/service-ca.crt
```

### MaaS PostgreSQL 준비
MaaS는 PostgreSQL 14 이상이 필요하며 RHOAI가 DB를 제공하지 않는다. 실습용 DB 이미지는 모델 이미지 레지스트리 `5010`에 반입해서 사용한다.

```bash
skopeo copy --src-tls-verify=false --dest-tls-verify=false \
  --src-creds '<MIRROR_REGISTRY_ID>:<MIRROR_REGISTRY_PW>' \
  --dest-creds '<MODEL_REGISTRY_ID>:<MODEL_REGISTRY_PW>' \
  docker://192.168.10.50:5000/ocp-mirror/rhel9/postgresql-16@sha256:d5842e96059ffa6020c22525014455637990543ffb126768d27b057cff2bb40a \
  docker://192.168.10.50:5010/rhel9/postgresql-16:rhoai-3.4
```

```bash
oc create namespace rhoai-maas-db --dry-run=client -o yaml | oc apply -f -
oc create secret docker-registry model-registry-pull \
  -n rhoai-maas-db \
  --docker-server=192.168.10.50:5010 \
  --docker-username='<MODEL_REGISTRY_ID>' \
  --docker-password='<MODEL_REGISTRY_PW>' \
  --dry-run=client -o yaml | oc apply -f -

oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: rhoai-maas-db
---
apiVersion: v1
kind: Secret
metadata:
  name: maas-postgresql
  namespace: rhoai-maas-db
type: Opaque
stringData:
  database-user: <MAAS_DB_ID>
  database-password: <MAAS_DB_PW>
  database-name: maas
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: maas-postgresql
  namespace: rhoai-maas-db
spec:
  storageClassName: truenas-nfs
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maas-postgresql
  namespace: rhoai-maas-db
spec:
  replicas: 1
  selector:
    matchLabels:
      app: maas-postgresql
  template:
    metadata:
      labels:
        app: maas-postgresql
    spec:
      imagePullSecrets:
        - name: model-registry-pull
      containers:
        - name: postgresql
          image: 192.168.10.50:5010/rhel9/postgresql-16:rhoai-3.4
          env:
            - name: POSTGRESQL_USER
              valueFrom:
                secretKeyRef:
                  name: maas-postgresql
                  key: database-user
            - name: POSTGRESQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: maas-postgresql
                  key: database-password
            - name: POSTGRESQL_DATABASE
              valueFrom:
                secretKeyRef:
                  name: maas-postgresql
                  key: database-name
          ports:
            - name: postgresql
              containerPort: 5432
          volumeMounts:
            - name: data
              mountPath: /var/lib/pgsql/data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: maas-postgresql
---
apiVersion: v1
kind: Service
metadata:
  name: maas-postgresql
  namespace: rhoai-maas-db
spec:
  selector:
    app: maas-postgresql
  ports:
    - name: postgresql
      port: 5432
      targetPort: postgresql
EOF

oc rollout status deployment/maas-postgresql -n rhoai-maas-db --timeout=300s
```

실습 DB는 cluster 내부 plain connection을 사용하지만 운영 환경은 TLS와 `sslmode=require`를 사용한다.

```bash
oc create secret generic maas-db-config \
  -n redhat-ods-applications \
  --from-literal=DB_CONNECTION_URL='postgresql://<MAAS_DB_ID>:<MAAS_DB_PW>@maas-postgresql.rhoai-maas-db.svc:5432/maas?sslmode=disable' \
  --dry-run=client -o yaml | oc apply -f -
```

### Gateway API 준비
```bash
oc get gatewayclass
oc get crd gateways.gateway.networking.k8s.io
```

OpenShift Gateway Controller용 GatewayClass와 `openshift-ingress/maas-default-gateway`를 준비한다. 현재 클러스터의 GatewayClass 이름을 확인해서 `gatewayClassName`에 사용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: maas-default-gateway
  namespace: openshift-ingress
  annotations:
    opendatahub.io/managed: "false"
    security.opendatahub.io/authorino-tls-bootstrap: "true"
    networking.istio.io/service-type: ClusterIP
spec:
  gatewayClassName: data-science-gateway-class
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: maas.apps.sno.ocp422.com
      tls:
        mode: Terminate
        certificateRefs:
          - kind: Secret
            name: router-certs-default
      allowedRoutes:
        namespaces:
          from: All
EOF
```

이 랩은 LoadBalancer controller가 없으므로 Gateway Service를 `ClusterIP`로 만들고 OpenShift Route의 passthrough TLS로 노출한다. Gateway의 `Programmed=True`와 Service의 `TYPE=ClusterIP`를 확인한다.

```bash
oc get gateway maas-default-gateway -n openshift-ingress
oc get service maas-default-gateway-data-science-gateway-class \
  -n openshift-ingress
```

```bash
oc apply -f - <<'EOF'
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: maas-default-gateway
  namespace: openshift-ingress
spec:
  host: maas.apps.sno.ocp422.com
  port:
    targetPort: 443
  tls:
    termination: passthrough
  to:
    kind: Service
    name: maas-default-gateway-data-science-gateway-class
    weight: 100
  wildcardPolicy: None
EOF
```

### Models-as-a-Service 활성화
```bash
oc patch dsc default-dsc --type=merge \
  -p '{"spec":{"components":{"kserve":{"modelsAsService":{"managementState":"Managed"}}}}}'

oc patch odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications --type=merge \
  -p '{"spec":{"dashboardConfig":{"modelAsService":true,"maasAuthPolicies":true}}}'
```

```bash
oc get crd | grep maas.opendatahub.io
oc get tenant -n models-as-a-service
oc get tenant default-tenant -n models-as-a-service -o yaml
oc get pods -n redhat-ods-applications | grep maas
```

`default-tenant`의 `READY`가 `True`이고 RHOAI 3.4.0 환경에서 reason이 `Reconciled`인지 확인한다.

### LLMInferenceService 배포
설치된 RHOAI가 제공하는 `LLMInferenceServiceConfig` 목록과 모델 URI 형식을 확인한다.

```bash
oc get llminferenceserviceconfig -n redhat-ods-applications
oc get llminferenceserviceconfig \
  v3-4-0-kserve-config-llm-template-nvidia-cuda \
  -n redhat-ods-applications -o yaml
```

모델은 disconnected 환경에 반입한 OCI ModelCar 또는 지원되는 내부 URI를 사용한다. 검증된 소형 모델은 `Qwen/Qwen2.5-0.5B-Instruct` commit `7ae557604adf67be50417f59c2c2f167def9a775`를 `/models`에 담은 ModelCar이며, 5010 registry의 `models/qwen2.5-0.5b-instruct:7ae5576`에 있다.

private registry에서 ModelCar를 pull하도록 `jukebox`에 pull secret을 만들고 default ServiceAccount에 연결한다.

```bash
oc create secret docker-registry model-registry-pull \
  -n jukebox \
  --docker-server=192.168.10.50:5010 \
  --docker-username='<MODEL_REGISTRY_ID>' \
  --docker-password='<MODEL_REGISTRY_PW>' \
  --dry-run=client -o yaml | oc apply -f -

oc secrets link default model-registry-pull -n jukebox --for=pull
```

```bash
oc apply -f - <<'EOF'
apiVersion: serving.kserve.io/v1alpha2
kind: LLMInferenceService
metadata:
  name: qwen-small
  namespace: jukebox
spec:
  baseRefs:
    - name: v3-4-0-kserve-config-llm-template-nvidia-cuda
  model:
    name: qwen2.5-0.5b-instruct
    uri: oci://192.168.10.50:5010/models/qwen2.5-0.5b-instruct:7ae5576
  replicas: 1
  router:
    route: {}
    gateway:
      refs:
        - name: maas-default-gateway
          namespace: openshift-ingress
  template:
    nodeSelector:
      lab-role: gpu
    containers:
      - name: main
        resources:
          requests:
            cpu: "4"
            memory: 12Gi
            nvidia.com/gpu: "1"
          limits:
            cpu: "8"
            memory: 24Gi
            nvidia.com/gpu: "1"
EOF

oc get llminferenceservice qwen-small -n jukebox -w
```

실제 config에서 요구하는 `baseRefs`, container name, model URI가 다르면 설치된 `LLMInferenceServiceConfig` 예제를 기준으로 수정한다. 단일 GPU 실습에서는 `router.scheduler: {}`를 넣지 않는다. 이를 넣으면 InferencePool 경로가 생성되며, 현재 랩 조합에서는 vLLM이 토큰을 생성해도 chat response body가 0바이트로 유실됐다.

### MaaS에 모델 publish
```bash
oc apply -f - <<'EOF'
apiVersion: maas.opendatahub.io/v1alpha1
kind: MaaSModelRef
metadata:
  name: qwen-small
  namespace: jukebox
spec:
  modelRef:
    kind: LLMInferenceService
    name: qwen-small
EOF

oc get maasmodelref qwen-small -n jukebox -o yaml
```

### Subscription과 authorization policy 생성
실제 계정명 대신 실습용 OpenShift Group을 사용한다.

```bash
oc adm groups new rhoai-maas-lab
oc adm groups add-users rhoai-maas-lab '<실습_사용자_ID>'
```

API key를 생성할 실제 OpenShift 사용자를 group에 추가한다. `kube:admin`처럼 `:`가 포함된 system username 대신 일반 실습 계정을 사용하는 편이 단순하다.

```bash
oc apply -f - <<'EOF'
apiVersion: maas.opendatahub.io/v1alpha1
kind: MaaSSubscription
metadata:
  name: rhoai-maas-lab
  namespace: models-as-a-service
spec:
  owner:
    groups:
      - name: rhoai-maas-lab
    users: []
  modelRefs:
    - name: qwen-small
      namespace: jukebox
      tokenRateLimits:
        - limit: 10000
          window: 1h
  priority: 100
---
apiVersion: maas.opendatahub.io/v1alpha1
kind: MaaSAuthPolicy
metadata:
  name: rhoai-maas-lab
  namespace: models-as-a-service
spec:
  subjects:
    groups:
      - name: rhoai-maas-lab
    users: []
  modelRefs:
    - name: qwen-small
      namespace: jukebox
EOF

oc get maassubscription,maasauthpolicy -n models-as-a-service
```

Subscription만 있고 authorization policy가 없으면 `403`, authorization policy만 있고 quota가 없으면 `429`가 발생한다.

### API key와 OpenAI 호환 API 검증
RHOAI 대시보드에서 실습용 API key를 발급한다. API key 값은 파일이나 문서에 저장하지 않고 현재 shell 환경변수로만 사용한다. `/maas-api` 관리 API는 OpenShift 로그인 토큰을 사용하고, 발급된 API key는 publish된 모델 endpoint에 사용한다.

```bash
read -rsp 'MaaS API key: ' MAAS_API_KEY
echo

curl -sk -H "Authorization: Bearer $(oc whoami -t)" \
  https://maas.apps.sno.ocp422.com/maas-api/v1/models | jq .

curl -sk https://maas.apps.sno.ocp422.com/jukebox/qwen-small/v1/chat/completions \
  -H "Authorization: Bearer $MAAS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5-0.5b-instruct","messages":[{"role":"user","content":"한 문장으로 자기소개해 주세요."}],"max_tokens":64}' | jq .

unset MAAS_API_KEY
```

### vLLM RawDeployment와 MaaS 비교
기존 `ServingRuntime + InferenceService(RawDeployment)`는 모델 서빙 자체를 확인하는 경로다. MaaS는 그 위에 subscription, authorization, API key, quota, consumption tracking을 추가하는 governance 계층이다.

| 항목 | vLLM RawDeployment | Models-as-a-Service |
|---|---|---|
| 모델 실행 | vLLM predictor | LLMInferenceService/지원 runtime |
| 인증 | 별도 Route/OAuth 구성 | MaaS API key |
| 권한 | 별도 RBAC/gateway policy | MaaSAuthPolicy |
| quota | 별도 rate limit | MaaSSubscription token limit |
| 사용량 | runtime metric 직접 구성 | MaaS consumption tracking |
