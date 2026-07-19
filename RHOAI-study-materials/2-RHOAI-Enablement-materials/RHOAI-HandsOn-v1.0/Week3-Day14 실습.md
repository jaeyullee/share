# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 실습
## week 3 - Day14

> **환경별 재확인**: GatewayClass 구현, RHCL/Kuadrant 의존 Operator, mTLS 경로, GPU 자원, model registry와 S3 endpoint는 검증 환경에 종속된다. 특히 OpenShift CIO GatewayClass가 아닌 환경에는 mTLS 제한을 그대로 적용하지 않는다. 공통 경계 조건은 [실습자료 검토 항목](<00-실습자료-검토항목.md#환경별-재확인>)을 참고한다.

> 사전 활성화: [Week1 Day1&2 - MaaS와 LLM API quota 구성](<Week1-Day1&2-환경구성.md#maas와-llm-api-quota-구성>), [GPU Workbench·서빙·학습 구성](<Week1-Day1&2-환경구성.md#gpu-workbench서빙학습-구성>), [Monitoring과 Guardrails 구성](<Week1-Day1&2-환경구성.md#monitoring과-guardrails-구성>)을 먼저 확인한다.

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

> RHCL 1.4.1은 `dns-operator 1.4.0`, `authorino-operator 1.4.1`, `limitador-operator 1.4.0`을 OLM 의존성으로 설치한다. 폐쇄망 카탈로그에 네 패키지와 operand 이미지가 모두 있어야 한다. OLM은 네 Operator를 같은 InstallPlan으로 설치하지만 dependency Operator와 RHCL 내부 Kuadrant controller의 기동 순서는 보장하지 않는다.

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

oc get csv,subscription -n openshift-operators | \
  grep -Ei 'rhcl|connectivity|dns-operator|authorino|limitador'
```

### OLM dependency 확인과 Kuadrant controller 재생성
Kuadrant CR을 만들기 전에 세 dependency CSV가 모두 `Succeeded`, Operator Deployment가 `Available`이고 Authorino와 Limitador CRD가 존재하는지 확인한다. CSV 설치 완료와 실제 controller 준비는 별도 상태이므로 둘 다 hard gate로 둔다.

```bash
for csv in \
  dns-operator.v1.4.0 \
  authorino-operator.v1.4.1 \
  limitador-operator.v1.4.0
do
  oc wait "csv/$csv" -n openshift-operators \
    --for=jsonpath='{.status.phase}'=Succeeded --timeout=5m
done

for deployment in \
  dns-operator-controller-manager \
  authorino-operator \
  limitador-operator-controller-manager
do
  oc wait "deployment/$deployment" -n openshift-operators \
    --for=condition=Available --timeout=5m
done

oc get crd \
  authorinos.operator.authorino.kuadrant.io \
  limitadors.limitador.kuadrant.io

oc get pods -n openshift-operators | \
  grep -E 'dns-operator|authorino-operator|limitador-operator'
```

RHCL Operator 패키지 안에서 `Kuadrant` CR을 처리하는 controller의 Pod 이름은 `kuadrant-operator-controller-manager-*`다. 별도 Kuadrant Operator를 설치하는 단계가 아니다. RHCL controller가 dependency CRD보다 먼저 시작하면 이후 Kuadrant CR을 생성해도 `MissingDependency` 상태가 유지될 수 있으므로, dependency 확인 후 controller Pod를 한 번 재생성한다.

```bash
KUADRANT_OPERATOR_POD=$(oc get pod -n openshift-operators \
  -l 'app=kuadrant,control-plane=controller-manager' \
  -o jsonpath='{.items[0].metadata.name}')

oc delete pod "$KUADRANT_OPERATOR_POD" -n openshift-operators

oc wait pod -n openshift-operators \
  -l 'app=kuadrant,control-plane=controller-manager' \
  --for=condition=Ready --timeout=5m

KUADRANT_OPERATOR_POD=$(oc get pod -n openshift-operators \
  -l 'app=kuadrant,control-plane=controller-manager' \
  -o jsonpath='{.items[0].metadata.name}')

if oc logs "$KUADRANT_OPERATOR_POD" -n openshift-operators \
  --since=5m | \
  grep -Ei '(authorino|limitador) operator is not installed'; then
  echo 'RHCL controller가 dependency를 인식하지 못했습니다.' >&2
  exit 1
fi

echo 'RHCL controller dependency 인식 확인 완료'
```

controller Pod 재생성은 Limitador Operator를 설치하는 작업이 아니다. 이미 설치된 CRD를 RHCL controller가 다시 discovery하게 한다. dependency 세 Operator를 RHCL보다 먼저 별도 설치했다면 재생성이 필요하지 않지만, RHCL Subscription이 OLM dependency를 함께 설치하는 기본 경로에서는 위 절차를 수행하는 편이 확실하다. OLM이 관리하는 Deployment는 직접 수정하지 않고 Pod만 삭제해 같은 선언으로 다시 생성한다.

### Kuadrant 인스턴스 생성
현재 CSV가 제공하는 CR 예제의 apiVersion을 먼저 확인한다. 조회 결과에서 `kind: Kuadrant`의 `apiVersion`을 아래 CR에 사용한다. RHCL 1.4.1의 현재 값은 `kuadrant.io/v1beta1`이다.

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

oc wait kuadrant/kuadrant -n kuadrant-system \
  --for=condition=Ready --timeout=10m
oc wait authorino/authorino -n kuadrant-system \
  --for=condition=Ready --timeout=5m
oc wait limitador/limitador -n kuadrant-system \
  --for=condition=Ready --timeout=5m
oc get kuadrant kuadrant -n kuadrant-system
oc get authorino,limitador -n kuadrant-system
oc get pods -n kuadrant-system
```

검증 환경의 `data-science-gateway-class`는 OpenShift CIO가 관리하는 Istio GatewayClass다. OCP 4.19 이상에서 이 토폴로지는 Kuadrant mTLS에 필요한 service-mesh sidecar 경로를 제공하지 않으므로 mTLS를 활성화하지 않는다. 활성화하면 Gateway에서 Authorino/Limitador로 가는 ext-auth gRPC가 `500`으로 실패한다.

```bash
oc patch kuadrant kuadrant -n kuadrant-system --type=merge \
  -p '{"spec":{"mtls":null}}'
oc get kuadrant kuadrant -n kuadrant-system
```

API key 인증 시 Authorino가 MaaS 내부 HTTPS endpoint의 OpenShift service CA를 신뢰하도록 CA를 mount한다. 이 설정이 없으면 OpenShift token 요청은 통과해도 MaaS API key 검증은 `403`으로 실패한다. 시스템 CA bundle과 service CA를 합친 파일을 실제 trust bundle 경로에 mount한다. `/etc/ssl/certs` 전체를 ConfigMap으로 덮으면 `ca-bundle.crt` symlink가 끊어지므로 사용하지 않는다.

```bash
SYSTEM_CA_FILE="$(mktemp)"
SERVICE_CA_FILE="$(mktemp)"
COMBINED_CA_FILE="$(mktemp)"
chmod 600 "$SYSTEM_CA_FILE" "$SERVICE_CA_FILE" "$COMBINED_CA_FILE"

oc exec -n kuadrant-system deployment/authorino -- \
  cat /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
  > "$SYSTEM_CA_FILE"

oc get configmap openshift-service-ca.crt -n kuadrant-system \
  -o jsonpath='{.data.service-ca\.crt}' > "$SERVICE_CA_FILE"

cat "$SYSTEM_CA_FILE" "$SERVICE_CA_FILE" > "$COMBINED_CA_FILE"

oc create configmap authorino-combined-ca \
  -n kuadrant-system \
  --from-file=tls-ca-bundle.pem="$COMBINED_CA_FILE" \
  --dry-run=client -o yaml | oc apply -f -

oc patch authorino authorino -n kuadrant-system --type=merge -p '
{"spec":{"volumes":{"items":[{
  "name":"combined-ca",
  "mountPath":"/etc/pki/ca-trust/extracted/pem",
  "configMaps":["authorino-combined-ca"],
  "items":[{"key":"tls-ca-bundle.pem","path":"tls-ca-bundle.pem"}]
}],"defaultMode":420}}}'

oc rollout status deployment/authorino -n kuadrant-system --timeout=300s

oc exec -n kuadrant-system deployment/authorino -- \
  test -s /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem

rm -f "$SYSTEM_CA_FILE" "$SERVICE_CA_FILE" "$COMBINED_CA_FILE"
unset SYSTEM_CA_FILE SERVICE_CA_FILE COMBINED_CA_FILE
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
DB_URL_FILE=$(mktemp)
chmod 600 "$DB_URL_FILE"

# DB 배포에 사용한 Secret에서 같은 ID/PW를 읽어 URL-encode하므로 값 불일치를 방지한다.
oc get secret maas-postgresql -n rhoai-maas-db -o json | jq -r '
  "postgresql://\(.data["database-user"] | @base64d | @uri):\(.data["database-password"] | @base64d | @uri)@maas-postgresql.rhoai-maas-db.svc:5432/\(.data["database-name"] | @base64d | @uri)?sslmode=disable"
' > "$DB_URL_FILE"

oc create secret generic maas-db-config \
  -n redhat-ods-applications \
  --from-file="DB_CONNECTION_URL=$DB_URL_FILE" \
  --dry-run=client -o yaml | oc apply -f -

rm -f "$DB_URL_FILE"
unset DB_URL_FILE
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

검증 환경에는 LoadBalancer controller가 없으므로 Gateway Service를 `ClusterIP`로 만들고 OpenShift Route의 passthrough TLS로 노출한다. Gateway의 `Programmed=True`와 Service의 `TYPE=ClusterIP`를 확인한다.

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

폐쇄망 catalog의 RHOAI 3.4.0에서 `maas-parameters`가 upstream `quay.io/opendatahub/*:latest`를 가리키면 image pull이 실패한다. 설치된 RHOAI CSV의 `relatedImages`에서 지원 image digest를 읽어 ConfigMap과 이미 생성된 Deployment를 일치시킨다.

```bash
RHOAI_CSV="$(oc get subscription rhods-operator \
  -n redhat-ods-operator -o jsonpath='{.status.currentCSV}')"

MAAS_API_IMAGE="$(oc get csv "$RHOAI_CSV" -n redhat-ods-operator \
  -o json | jq -er '.spec.relatedImages[] |
  select(.name == "odh_maas_api_image") | .image')"
MAAS_CONTROLLER_IMAGE="$(oc get csv "$RHOAI_CSV" -n redhat-ods-operator \
  -o json | jq -er '.spec.relatedImages[] |
  select(.name == "odh_maas_controller_image") | .image')"
PAYLOAD_IMAGE="$(oc get csv "$RHOAI_CSV" -n redhat-ods-operator \
  -o json | jq -er '.spec.relatedImages[] |
  select(.name == "odh_ai_gateway_payload_processing_image") | .image')"

oc patch configmap maas-parameters -n redhat-ods-applications \
  --type=merge -p "$(jq -n \
  --arg api "$MAAS_API_IMAGE" \
  --arg controller "$MAAS_CONTROLLER_IMAGE" \
  --arg payload "$PAYLOAD_IMAGE" '{data:{
    "maas-api-image":$api,
    "maas-controller-image":$controller,
    "payload-processing-image":$payload
  }}')"

oc set image deployment/maas-api -n redhat-ods-applications \
  maas-api="$MAAS_API_IMAGE"
oc set image deployment/maas-controller -n redhat-ods-applications \
  manager="$MAAS_CONTROLLER_IMAGE"
oc set image deployment/payload-processing -n openshift-ingress \
  payload-processing="$PAYLOAD_IMAGE"
```

`openshift-ingress-deny-all` NetworkPolicy가 있는 환경에서는 payload processor가 Kubernetes API에 접근하고 MaaS Gateway가 gRPC 9004로 호출할 수 있도록 명시적으로 허용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payload-processing-allow
  namespace: openshift-ingress
spec:
  podSelector:
    matchLabels:
      app: payload-processing
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              gateway.networking.k8s.io/gateway-name: maas-default-gateway
      ports:
        - protocol: TCP
          port: 9004
  egress:
    - {}
EOF

oc rollout status deployment/maas-api \
  -n redhat-ods-applications --timeout=300s
oc rollout status deployment/maas-controller \
  -n redhat-ods-applications --timeout=300s
oc rollout restart deployment/payload-processing -n openshift-ingress
oc rollout status deployment/payload-processing \
  -n openshift-ingress --timeout=300s
```

Kuadrant WASM Service가 준비되기 전에 MaaS Gateway Pod가 시작되면 remote load 실패가 캐시되어 모든 요청이 `503 wasm_fail_stream`이 될 수 있다. Gateway를 한 번 재시작하고 WASM fetch success와 health를 확인한다.

```bash
oc rollout restart \
  deployment/maas-default-gateway-data-science-gateway-class \
  -n openshift-ingress
oc rollout status \
  deployment/maas-default-gateway-data-science-gateway-class \
  -n openshift-ingress --timeout=300s

MAAS_GATEWAY_POD="$(oc get pod -n openshift-ingress \
  -l gateway.networking.k8s.io/gateway-name=maas-default-gateway \
  -o jsonpath='{.items[0].metadata.name}')"
oc exec -n openshift-ingress "$MAAS_GATEWAY_POD" -- \
  pilot-agent request GET 'stats?filter=wasm.remote_load'

curl -skf https://maas.apps.sno.ocp422.com/maas-api/health | jq .

unset RHOAI_CSV MAAS_API_IMAGE MAAS_CONTROLLER_IMAGE PAYLOAD_IMAGE
unset MAAS_GATEWAY_POD
```

### LLMInferenceServiceConfig 확인
설치된 RHOAI가 제공하는 `LLMInferenceServiceConfig` 목록과 모델 URI 형식을 확인한다.

```bash
oc get llminferenceserviceconfig -n redhat-ods-applications
oc get llminferenceserviceconfig \
  v3-4-0-kserve-config-llm-template-nvidia-cuda \
  -n redhat-ods-applications -o yaml
```

### Qwen ModelCar 폐쇄망 반입
모델은 외부 연결 구간에서 특정 commit으로 고정해 내려받고 OCI archive로 만든 다음 폐쇄망에 전달한다. 이 실습에서는 `Qwen/Qwen2.5-0.5B-Instruct` commit `7ae557604adf67be50417f59c2c2f167def9a775`를 사용한다. 7자리 값 `7ae5576`은 내부 image tag이고, 실제 다운로드에는 전체 commit을 사용한다.

ModelCar는 vLLM 실행 image가 아니라 model weight, tokenizer, config를 `/models`에 담은 OCI image다. build context, OCI archive와 Podman local storage를 위해 약 4 GiB의 여유 공간을 준비한다. 다음 명령은 인터넷과 `registry.access.redhat.com`에 접근할 수 있고 Python 3와 Podman이 설치된 **외부 연결 호스트**에서 실행한다.

```bash
MODEL_REPO='Qwen/Qwen2.5-0.5B-Instruct'
MODEL_REVISION='7ae557604adf67be50417f59c2c2f167def9a775'
MODEL_TAG="${MODEL_REVISION:0:7}"
WORK_DIR="$HOME/day14-modelcar"
LOCAL_IMAGE="localhost/qwen2.5-0.5b-instruct:${MODEL_TAG}"

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR/context/models"

python3 -m venv "$WORK_DIR/.venv"
source "$WORK_DIR/.venv/bin/activate"
python -m pip install --upgrade pip huggingface_hub

# branch나 latest가 아니라 전체 commit으로 model snapshot을 고정한다.
hf download "$MODEL_REPO" \
  --revision "$MODEL_REVISION" \
  --local-dir "$WORK_DIR/context/models"

rm -rf "$WORK_DIR/context/models/.cache"
printf '%s\n' "$MODEL_REPO" > "$WORK_DIR/context/models/SOURCE_REPOSITORY"
printf '%s\n' "$MODEL_REVISION" > "$WORK_DIR/context/models/SOURCE_REVISION"

test -s "$WORK_DIR/context/models/config.json"
test -s "$WORK_DIR/context/models/tokenizer.json"
find "$WORK_DIR/context/models" -maxdepth 1 -name '*.safetensors' \
  -type f -size +0c | grep -q .
```

RHOAI/KServe가 임의 UID와 root group으로 ModelCar를 읽을 수 있도록 shell이 있는 UBI base, `/models`, read/execute permission, non-root user를 사용한다. `scratch` base는 KServe가 model file 접근을 준비할 shell이 없어 사용하지 않는다.

```bash
cat > "$WORK_DIR/context/Containerfile" <<'EOF'
FROM registry.access.redhat.com/ubi9/ubi-micro:9.6
COPY --chown=0:0 models /models
RUN chmod -R a=rX /models
USER 65534
EOF

podman build --format=oci \
  -t "$LOCAL_IMAGE" "$WORK_DIR/context"

podman run --rm --entrypoint /bin/sh "$LOCAL_IMAGE" -c '
  test -r /models/config.json
  test -r /models/tokenizer.json
  test -r /models/model.safetensors
'

ARCHIVE="$WORK_DIR/qwen2.5-0.5b-instruct-${MODEL_TAG}.oci.tar"
podman save --format=oci-archive -o "$ARCHIVE" "$LOCAL_IMAGE"
(
  cd "$WORK_DIR"
  sha256sum "$(basename "$ARCHIVE")" > "$(basename "$ARCHIVE").sha256"
)

deactivate 2>/dev/null || true
ls -lh "$ARCHIVE" "$ARCHIVE.sha256"
```

생성된 OCI archive와 `.sha256` 파일을 승인된 이동식 매체나 파일 전송 절차로 Bastion에 전달한다. archive checksum은 OCI image digest와 목적이 다르다. 전자는 전달 중 파일 손상을 확인하고, 후자는 registry에 저장된 image manifest를 식별한다.

다음 명령은 **폐쇄망 Bastion**에서 실행한다. `<반입_디렉터리>`에는 전달받은 두 파일이 있어야 한다.

```bash
MODEL_REVISION='7ae557604adf67be50417f59c2c2f167def9a775'
MODEL_TAG="${MODEL_REVISION:0:7}"
IMPORT_DIR='<반입_디렉터리>'
ARCHIVE="$IMPORT_DIR/qwen2.5-0.5b-instruct-${MODEL_TAG}.oci.tar"
LOCAL_IMAGE="localhost/qwen2.5-0.5b-instruct:${MODEL_TAG}"
DEST_IMAGE="192.168.10.50:5010/models/qwen2.5-0.5b-instruct:${MODEL_TAG}"
AUTH_FILE=/tmp/day14-model-registry-auth.json
DIGEST_FILE=/tmp/day14-modelcar.digest

(
  cd "$IMPORT_DIR"
  sha256sum -c "$(basename "$ARCHIVE").sha256"
)

podman load -i "$ARCHIVE"
podman login --tls-verify=false --authfile "$AUTH_FILE" \
  -u '<MODEL_REGISTRY_ID>' -p '<MODEL_REGISTRY_PW>' \
  192.168.10.50:5010

podman tag "$LOCAL_IMAGE" "$DEST_IMAGE"
podman push --tls-verify=false --authfile "$AUTH_FILE" \
  --digestfile "$DIGEST_FILE" "$DEST_IMAGE"

PUSHED_DIGEST=$(cat "$DIGEST_FILE")
REGISTRY_DIGEST=$(skopeo inspect --tls-verify=false \
  --authfile "$AUTH_FILE" --format '{{.Digest}}' \
  "docker://$DEST_IMAGE")

printf 'Pushed digest:   %s\nRegistry digest: %s\n' \
  "$PUSHED_DIGEST" "$REGISTRY_DIGEST"
test "$PUSHED_DIGEST" = "$REGISTRY_DIGEST"

rm -f "$AUTH_FILE" "$DIGEST_FILE"
```

`sha256sum`이 `OK`이고 두 registry digest가 같아야 한다. 현재 5010 registry에는 이 ModelCar가 미리 준비되어 있지 않으므로 위 push를 완료한 뒤 다음 단계로 진행한다.

참조: [Red Hat OpenShift AI 3.4 - Deploying models](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/pdf/deploying_models/Red_Hat_OpenShift_AI_Self-Managed-3.4-Deploying_models-en-US.pdf), [Hugging Face Hub - Download files](https://huggingface.co/docs/huggingface_hub/guides/download)

### LLMInferenceService 배포

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

실제 config에서 요구하는 `baseRefs`, container name, model URI가 다르면 설치된 `LLMInferenceServiceConfig` 예제를 기준으로 수정한다. 단일 GPU 실습에서는 `router.scheduler: {}`를 넣지 않는다. 이를 넣으면 InferencePool 경로가 생성되며, 검증된 구성 조합에서는 vLLM이 토큰을 생성해도 chat response body가 0바이트로 유실됐다.

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
MaaS API key를 발급할 일반 OpenShift OAuth 사용자를 HTPasswd identity provider에 추가한다. 기존 provider가 있으면 HTPasswd 파일을 추출해 다른 계정을 보존하고, 없으면 Secret과 provider를 처음 생성한다. 비밀번호는 문서나 shell history에 직접 기록하지 않고 대화형 입력으로만 받는다.

```bash
command -v htpasswd >/dev/null || sudo dnf install -y httpd-tools

MAAS_USER='rhoai-maas-lab-user'
read -rsp 'MaaS lab user password: ' MAAS_PASSWORD
echo

HTPASSWD_SECRET=$(oc get oauth cluster \
  -o jsonpath='{.spec.identityProviders[?(@.type=="HTPasswd")].htpasswd.fileData.name}')
HTPASSWD_PROVIDER_EXISTS=false
if test -n "$HTPASSWD_SECRET"; then
  HTPASSWD_PROVIDER_EXISTS=true
else
  HTPASSWD_SECRET=htpass-secret
fi

HTPASSWD_DIR=$(mktemp -d)
if oc get "secret/$HTPASSWD_SECRET" -n openshift-config >/dev/null 2>&1; then
  oc extract "secret/$HTPASSWD_SECRET" -n openshift-config \
    --to="$HTPASSWD_DIR" --confirm
else
  touch "$HTPASSWD_DIR/htpasswd"
fi

htpasswd -B -b "$HTPASSWD_DIR/htpasswd" "$MAAS_USER" "$MAAS_PASSWORD"

if oc get "secret/$HTPASSWD_SECRET" -n openshift-config >/dev/null 2>&1; then
  oc set data "secret/$HTPASSWD_SECRET" -n openshift-config \
    --from-file="htpasswd=$HTPASSWD_DIR/htpasswd"
else
  oc create secret generic "$HTPASSWD_SECRET" -n openshift-config \
    --from-file="htpasswd=$HTPASSWD_DIR/htpasswd"
fi
rm -rf "$HTPASSWD_DIR"

# HTPasswd provider가 없던 클러스터에서는 기존 provider 배열을 보존해 추가한다.
if test "$HTPASSWD_PROVIDER_EXISTS" = false; then
  OAUTH_PATCH=$(oc get oauth cluster -o json | jq -c \
    --arg secret "$HTPASSWD_SECRET" \
    '{spec:{identityProviders:((.spec.identityProviders // []) + [{
      name:"htpasswd",
      mappingMethod:"claim",
      type:"HTPasswd",
      htpasswd:{fileData:{name:$secret}}
    }])}}')
  oc patch oauth cluster --type=merge -p "$OAUTH_PATCH"
fi

oc get oauth cluster \
  -o jsonpath='{range .spec.identityProviders[*]}{.name}{"\t"}{.type}{"\n"}{end}'

# 관리자 kubeconfig를 바꾸지 않고 별도 kubeconfig로 새 사용자의 로그인을 확인한다.
OCP_API=$(oc whoami --show-server)
MAAS_KUBECONFIG=/tmp/day14-maas-user.kubeconfig
rm -f "$MAAS_KUBECONFIG"
KUBECONFIG="$MAAS_KUBECONFIG" oc login "$OCP_API" \
  -u "$MAAS_USER" -p "$MAAS_PASSWORD"
KUBECONFIG="$MAAS_KUBECONFIG" oc whoami

# Subscription과 policy는 개인 계정보다 실습용 Group을 대상으로 연결한다.
oc adm groups new rhoai-maas-lab 2>/dev/null || true
oc adm groups add-users rhoai-maas-lab "$MAAS_USER"
oc get group rhoai-maas-lab -o yaml
```

`kube:admin`처럼 `:`가 포함된 system username 대신 위에서 만든 일반 OAuth 계정을 사용한다. HTPasswd Secret 변경이 OAuth server에 반영되기까지 잠시 걸리면 몇 초 뒤 `oc login`을 다시 실행한다.

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

`owner.groups`와 `subjects.groups`의 항목은 `{name: <GROUP>}` 객체지만, 특정 사용자를 직접 지정하는 `owner.users`와 `subjects.users`의 항목은 사용자명 문자열이다.

### API key와 OpenAI 호환 API 검증
RHOAI 대시보드에서 발급하거나 `/maas-api/v1/api-keys`로 직접 생성한다. API key 원문은 생성 응답에서 한 번만 반환되므로 파일이나 문서에 저장하지 않고 현재 shell 변수로만 사용한다. 아래 명령은 앞에서 만든 일반 OpenShift OAuth 사용자의 임시 kubeconfig에서 token을 가져온다. 클라이언트 인증서 기반 관리자 kubeconfig는 `oc whoami -t`로 token을 반환하지 않는다.

```bash
OPENSHIFT_TOKEN=$(KUBECONFIG="$MAAS_KUBECONFIG" oc whoami -t)

API_KEY_RESPONSE=$(curl -sk -X POST \
  https://maas.apps.sno.ocp422.com/maas-api/v1/api-keys \
  -H "Authorization: Bearer $OPENSHIFT_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"day14-lab","description":"Day14 validation","subscription":"rhoai-maas-lab","expiresIn":"1h"}')

MAAS_API_KEY=$(jq -r '.key' <<<"$API_KEY_RESPONSE")
MAAS_API_KEY_ID=$(jq -r '.id' <<<"$API_KEY_RESPONSE")
test "${MAAS_API_KEY#sk-oai-}" != "$MAAS_API_KEY"

curl -sk -H "Authorization: Bearer $MAAS_API_KEY" \
  https://maas.apps.sno.ocp422.com/maas-api/v1/models | jq .

curl -sk https://maas.apps.sno.ocp422.com/jukebox/qwen-small/v1/chat/completions \
  -H "Authorization: Bearer $MAAS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5-0.5b-instruct","messages":[{"role":"user","content":"한 문장으로 자기소개해 주세요."}],"max_tokens":64}' | jq .

curl -sk -X DELETE \
  -H "Authorization: Bearer $OPENSHIFT_TOKEN" \
  "https://maas.apps.sno.ocp422.com/maas-api/v1/api-keys/$MAAS_API_KEY_ID" | jq .

# 폐기한 key는 더 이상 사용할 수 없어야 한다.
curl -sk -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer $MAAS_API_KEY" \
  https://maas.apps.sno.ocp422.com/maas-api/v1/models

rm -f "$MAAS_KUBECONFIG"
unset API_KEY_RESPONSE MAAS_API_KEY MAAS_API_KEY_ID OPENSHIFT_TOKEN
unset MAAS_PASSWORD MAAS_KUBECONFIG OCP_API OAUTH_PATCH
unset HTPASSWD_SECRET HTPASSWD_DIR HTPASSWD_PROVIDER_EXISTS
```

2026-07-12 검증에서는 key 생성 `201`, 모델 목록 `200`, Qwen chat completion `200`, key 폐기 `200`, 폐기된 key 재사용 `403`을 확인했다.

### vLLM RawDeployment와 MaaS 비교
기존 `ServingRuntime + InferenceService(RawDeployment)`는 모델 서빙 자체를 확인하는 경로다. MaaS는 그 위에 subscription, authorization, API key, quota, consumption tracking을 추가하는 governance 계층이다.

| 항목 | vLLM RawDeployment | Models-as-a-Service |
|---|---|---|
| 모델 실행 | vLLM predictor | LLMInferenceService/지원 runtime |
| 인증 | 별도 Route/OAuth 구성 | MaaS API key |
| 권한 | 별도 RBAC/gateway policy | MaaSAuthPolicy |
| quota | 별도 rate limit | MaaSSubscription token limit |
| 사용량 | runtime metric 직접 구성 | MaaS consumption tracking |
