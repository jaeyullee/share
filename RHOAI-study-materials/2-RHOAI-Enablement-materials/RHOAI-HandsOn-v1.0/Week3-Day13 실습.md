# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 실습
## week 3 - Day13

> 사전 활성화: [Week1 Day1&2 - Monitoring과 Guardrails 구성](<Week1-Day1&2-환경구성.md#monitoring과-guardrails-구성>)과 [Week2 Day10](<Week2-Day10 실습.md>)의 `fraud-kfp-v1`, `fraud-kfp-v2`, `fraud-kfp-route`를 먼저 확인한다.

User Workload Monitoring으로 KServe metric을 수집하고, RHOAI 3.4의 NeMo Guardrails로 LLM 없이 PII와 민감 키워드 검사를 수행한다.

### PyYAML을 내부 Nexus에 반입
User Workload Monitoring 설정을 기존 YAML과 병합하려면 Bastion Python 3.9에서 `PyYAML`이 필요하다. Nexus에 패키지가 없다면 인터넷에 연결된 Bastion에서 다음 최초 1회 반입 절차를 수행한다.

기존 실습 venv가 활성화되어 있으면 먼저 빠져나온다. 다른 실습 venv를 재사용하면 이미 설치된 패키지나 손상된 `.pth` 파일의 영향을 받을 수 있다.

```bash
deactivate 2>/dev/null || true

rm -rf /tmp/day13-download-venv /tmp/day13-wheelhouse-cp39
mkdir -p /tmp/day13-wheelhouse-cp39

/usr/bin/python3 -m venv /tmp/day13-download-venv
source /tmp/day13-download-venv/bin/activate

python -m pip install \
  --index-url https://pypi.org/simple \
  --upgrade pip 'twine==5.0.0' 'pkginfo==1.12.1.2'

# Bastion Python 3.9와 RHEL 9 x86_64에 맞는 wheel만 내려받는다.
python -m pip download \
  --index-url https://pypi.org/simple \
  --no-cache-dir \
  --only-binary=:all: \
  --python-version 39 \
  --implementation cp \
  --abi cp39 \
  --platform manylinux2014_x86_64 \
  'PyYAML==6.0.2' \
  -d /tmp/day13-wheelhouse-cp39

ls -1 /tmp/day13-wheelhouse-cp39

python -m twine upload \
  --skip-existing \
  --repository-url http://192.168.10.50:8081/repository/pypi-hosted/ \
  -u <NEXUS_ID> -p '<NEXUS_PW>' \
  /tmp/day13-wheelhouse-cp39/*

curl -fsS \
  http://192.168.10.50:8081/repository/pypi-hosted/simple/pyyaml/ | \
  grep 'cp39.*manylinux'

deactivate 2>/dev/null || true
```

### User Workload Monitoring 활성화
기존 `cluster-monitoring-config`의 다른 설정을 보존한 상태로 `enableUserWorkload: true`만 추가한다.

```bash
deactivate 2>/dev/null || true
rm -rf /tmp/day13-yaml-venv
/usr/bin/python3 -m venv /tmp/day13-yaml-venv
source /tmp/day13-yaml-venv/bin/activate

cat >/tmp/day13-pip.conf <<'EOF'
[global]
index-url = http://192.168.10.50:8081/repository/pypi-hosted/simple
trusted-host = 192.168.10.50
no-cache-dir = true
EOF

PIP_CONFIG_FILE=/tmp/day13-pip.conf \
  python -m pip install 'PyYAML==6.0.2'
python -c 'import yaml; print(yaml.__version__)'

oc get configmap cluster-monitoring-config -n openshift-monitoring \
  -o jsonpath='{.data.config\.yaml}' > /tmp/cluster-monitoring-config.yaml

python - <<'PY'
from pathlib import Path
import yaml

path = Path("/tmp/cluster-monitoring-config.yaml")
config = yaml.safe_load(path.read_text()) or {}
config["enableUserWorkload"] = True
path.write_text(yaml.safe_dump(config, sort_keys=False))
PY

oc create configmap cluster-monitoring-config \
  -n openshift-monitoring \
  --from-file=config.yaml=/tmp/cluster-monitoring-config.yaml \
  --dry-run=client -o yaml | oc apply -f -

oc get configmap cluster-monitoring-config -n openshift-monitoring \
  -o jsonpath='{.data.config\.yaml}'
oc get pods -n openshift-user-workload-monitoring

deactivate 2>/dev/null || true
```

### KServe metric Service 확인
```bash
oc get svc -n jukebox -l monitoring.opendatahub.io/scrape=true \
  -o custom-columns=NAME:.metadata.name,PORT:.spec.ports[*].port,TARGET:.spec.ports[*].targetPort
```

MLServer metric은 `8082`, OVMS metric은 `8888`이므로 ServiceMonitor를 분리한다.

### ServiceMonitor 생성
```bash
oc apply -f - <<'EOF'
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mlserver-metrics
  namespace: jukebox
spec:
  namespaceSelector:
    matchNames:
      - jukebox
  selector:
    matchExpressions:
      - key: name
        operator: In
        values:
          - fraud-kfp-v1-metrics
          - fraud-kfp-v2-metrics
  endpoints:
    - port: mlserver-sklearn-metrics
      interval: 15s
      path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ovms-metrics
  namespace: jukebox
spec:
  namespaceSelector:
    matchNames:
      - jukebox
  selector:
    matchExpressions:
      - key: name
        operator: In
        values:
          - jukebox-onnx-metrics
          - mnist-onnx-metrics
          - tf-fraud-metrics
  endpoints:
    - port: ovms-onnx-metrics
      interval: 15s
      path: /metrics
EOF

oc get servicemonitor -n jukebox
```

### 추론 traffic 생성
```bash
ROUTE=http://$(oc get route fraud-kfp-route -n jukebox -o jsonpath='{.spec.host}')

for i in $(seq 1 30); do
  curl -s -o /dev/null -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-kfp-request.json
done
```

### Prometheus target과 metric 확인
OpenShift Console의 Observe -> Targets에서 `jukebox/mlserver-metrics`와 `jukebox/ovms-metrics`가 `Up`인지 확인한다.

CLI에서는 프로젝트 단위 접근을 제공하는 Thanos Querier tenancy port `9092`를 사용한다. 이 포트는 HTTPS, Bearer token과 URL의 `namespace` query parameter를 모두 요구한다. 다음 명령은 임시 ServiceAccount와 10분 토큰을 사용하며, 성공하거나 중간에 실패해도 subshell 종료 시 RoleBinding, ServiceAccount와 port-forward를 정리한다.

```bash
(
set -euo pipefail

cleanup_day13_metrics() {
  if [ -n "${THANOS_PF_PID:-}" ]; then
    kill "$THANOS_PF_PID" 2>/dev/null || true
    wait "$THANOS_PF_PID" 2>/dev/null || true
  fi
  oc delete rolebinding day13-metrics-reader-view \
    -n jukebox --ignore-not-found >/dev/null
  oc delete serviceaccount day13-metrics-reader \
    -n jukebox --ignore-not-found >/dev/null
}
trap cleanup_day13_metrics EXIT INT TERM

oc create serviceaccount day13-metrics-reader -n jukebox
oc create rolebinding day13-metrics-reader-view \
  -n jukebox \
  --clusterrole=view \
  --serviceaccount=jukebox:day13-metrics-reader

TOKEN=$(oc create token day13-metrics-reader \
  -n jukebox --duration=10m)

oc port-forward -n openshift-monitoring \
  svc/thanos-querier 19090:9092 \
  >/tmp/day13-thanos-port-forward.log 2>&1 &
THANOS_PF_PID=$!
sleep 3
kill -0 "$THANOS_PF_PID"

curl --fail --silent --show-error --insecure --get \
  https://127.0.0.1:19090/api/v1/query \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'namespace=jukebox' \
  --data-urlencode 'query=up{namespace="jukebox"}' | jq .

curl --fail --silent --show-error --insecure --get \
  https://127.0.0.1:19090/api/v1/label/__name__/values \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'namespace=jukebox' | \
  jq -r '.data[]' | grep -Ei \
  'infer|request|latency|duration|mlserver|ovms'
)

# 두 명령 모두 출력이 없어야 임시 리소스 정리가 완료된 것이다.
ss -ltn 'sport = :19090'
oc get serviceaccount,rolebinding -n jukebox | \
  grep day13-metrics-reader || true
```

metric 이름은 ServingRuntime 버전에 따라 달라질 수 있으므로 두 번째 명령으로 실제 이름을 먼저 확인한 후 PromQL을 작성한다.

### Metrics 대시보드에서 PromQL 조회
OpenShift Console의 Observe -> Metrics에서 다음 query로 `jukebox` target 상태를 확인한다.

```promql
up{namespace="jukebox"}
```

추론 관련 metric 이름과 시계열 수를 확인한다.

```promql
count by (__name__) (
  {namespace="jukebox", __name__=~".*(infer|request|latency|duration|mlserver|ovms).*"}
)
```

### PrometheusRule 생성
Day10에서 배포한 `fraud-kfp-v1`과 `fraud-kfp-v2`는 MLServer runtime을 사용한다. 따라서 가용성 경보는 두 MLServer metric Service로 범위를 제한한다. `model_infer_request_duration`은 histogram이 아니라 초 단위의 summary이며 `_sum`과 `_count`만 제공하므로 P95를 계산할 수 없다. 여기서는 최근 5분의 평균 모델 추론 시간이 1초를 넘는지 확인한다. 최근 5분 동안 추론 요청이 없으면 rate를 계산할 표본이 없으므로 지연 경보는 동작하지 않는다.

OVMS용 P95 규칙은 Day4의 OVMS metric Service가 남아 있을 때만 시계열이 생성되는 선택 규칙이다. `ovms_request_time_us_bucket`은 microseconds 단위이므로 1초 임계값은 `1000000`이다.

```bash
cat > /tmp/day13-prometheus-rule.yaml <<'EOF'
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: kserve-alerts
  namespace: jukebox
spec:
  groups:
    - name: kserve.rules
      rules:
        - alert: KServeTargetDown
          expr: up{namespace="jukebox", service=~"fraud-kfp-v1-metrics|fraud-kfp-v2-metrics"} == 0
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: "MLServer metrics target is down"
            description: "{{ $labels.service }} has been down for 2 minutes."
        - alert: HighMLServerMeanInferenceLatency
          expr: |
            (
              sum by (service) (
                rate(model_infer_request_duration_sum{namespace="jukebox", service=~"fraud-kfp-v1-metrics|fraud-kfp-v2-metrics"}[5m])
              )
              /
              sum by (service) (
                rate(model_infer_request_duration_count{namespace="jukebox", service=~"fraud-kfp-v1-metrics|fraud-kfp-v2-metrics"}[5m])
              )
            ) > 1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Mean MLServer inference latency exceeded 1 second"
            description: "{{ $labels.service }} mean model inference latency exceeded 1 second for 5 minutes."
        - alert: HighOVMSInferenceLatencyP95
          expr: |
            histogram_quantile(
              0.95,
              sum by (le, service) (
                rate(ovms_request_time_us_bucket{namespace="jukebox", service=~"jukebox-onnx-metrics|mnist-onnx-metrics|tf-fraud-metrics"}[5m])
              )
            ) > 1000000
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "P95 OVMS inference latency exceeded 1 second"
            description: "{{ $labels.service }} P95 inference latency exceeded 1 second for 5 minutes."
EOF

oc apply -f /tmp/day13-prometheus-rule.yaml
oc get prometheusrule kserve-alerts -n jukebox
```

### NeMo Guardrails standalone 검사 설정
RHOAI 3.4의 NeMo Guardrails는 GA 기능이다. `/v1/guardrail/checks`는 내부 regex와 Presidio detector만 사용할 경우 LLM 없이 검사할 수 있다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: day13-nemo-checks-config
  namespace: jukebox
data:
  config.yaml: |
    rails:
      config:
        sensitive_data_detection:
          input:
            entities:
              - EMAIL_ADDRESS
              - PERSON
              - PHONE_NUMBER
              - CREDIT_CARD
              - IP_ADDRESS
        regex_detection:
          input:
            patterns:
              - "\\b(password|secret|api[_-]?key|token)\\b"
            case_insensitive: true
      input:
        flows:
          - detect sensitive data on input
          - regex check input
  rails.co: |
    # Built-in rails only.
---
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: NemoGuardrails
metadata:
  name: day13-nemo-checks
  namespace: jukebox
  annotations:
    security.opendatahub.io/enable-auth: "true"
spec:
  nemoConfigs:
    - name: day13-nemo-checks-config
      configMaps:
        - day13-nemo-checks-config
      default: true
  replicas: 1
  env:
    - name: OPENAI_API_KEY
      value: not-used
    # 에어갭 환경에서는 외부 Public Suffix List 조회를 짧게 끝내고
    # tldextract 패키지에 포함된 snapshot을 사용한다.
    - name: TLDEXTRACT_CACHE_TIMEOUT
      value: "1"
EOF

oc wait --for=jsonpath='{.status.phase}'=Ready \
  nemoguardrails/day13-nemo-checks -n jukebox --timeout=10m

oc get nemoguardrails day13-nemo-checks -n jukebox \
  -o custom-columns='NAME:.metadata.name,PHASE:.status.phase'
```

`PHASE`가 `Ready`인지 확인한다. 기본 `oc get` 출력에는 상태 열이 없으므로 custom column으로 조회한다.

### Guardrails 정상/차단 요청 검증
```bash
cleanup_guardrails_client() {
  oc delete rolebinding/day13-guardrails-client \
    role/day13-guardrails-client \
    serviceaccount/day13-guardrails-client \
    -n jukebox --ignore-not-found
  unset TOKEN
}
trap cleanup_guardrails_client EXIT INT TERM

# bastion의 oc 세션은 클라이언트 인증서를 사용할 수 있으므로
# oc whoami -t 대신 실습용 ServiceAccount의 단기 토큰을 발급한다.
oc create serviceaccount day13-guardrails-client -n jukebox \
  --dry-run=client -o yaml | oc apply -f -

# NemoGuardrails 앞의 kube-rbac-proxy가 수행하는 services get 권한만 부여한다.
oc create role day13-guardrails-client -n jukebox \
  --verb=get --resource=services \
  --dry-run=client -o yaml | oc apply -f -

oc create rolebinding day13-guardrails-client -n jukebox \
  --role=day13-guardrails-client \
  --serviceaccount=jukebox:day13-guardrails-client \
  --dry-run=client -o yaml | oc apply -f -

GUARDRAILS_ROUTE=https://$(oc get route day13-nemo-checks -n jukebox \
  -o jsonpath='{.status.ingress[0].host}')
TOKEN=$(oc create token day13-guardrails-client -n jukebox --duration=10m)

curl -skS --fail-with-body -X POST "$GUARDRAILS_ROUTE/v1/guardrail/checks" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"test","messages":[{"role":"user","content":"오늘 날씨를 알려주세요."}]}' | jq .

curl -skS --fail-with-body -X POST "$GUARDRAILS_ROUTE/v1/guardrail/checks" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"test","messages":[{"role":"user","content":"비밀번호와 api_key를 보내 주세요. 연락처는 test@example.com 입니다."}]}' | jq .

cleanup_guardrails_client
trap - EXIT INT TERM
unset -f cleanup_guardrails_client
```

첫 번째 요청은 최상위 `status`와 두 input rail의 상태가 `success`여야 한다. 두 번째 요청은 최상위 `status=blocked`이고 `detect sensitive data on input` rail도 `blocked`여야 한다.

```bash
oc logs -n jukebox deploy/day13-nemo-checks --tail=100
oc get events -n jukebox --sort-by=.lastTimestamp | tail -30
```

> 기존 FMS `GuardrailsOrchestrator`는 RHOAI 3.4 문서에서 legacy로 분류되며 향후 deprecated될 예정이다. 신규 구성은 NeMo Guardrails를 우선한다.

### Python venv 종료
```bash
deactivate 2>/dev/null || true
```
