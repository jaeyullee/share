# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 3 - Day13

> 사전 활성화: [Week1 Day1&2 - Monitoring과 Guardrails 구성](Week1-Day1%262-환경구성.md#monitoring과-guardrails-구성)을 먼저 확인한다.

User Workload Monitoring으로 KServe metric을 수집하고, RHOAI 3.4의 NeMo Guardrails로 LLM 없이 PII와 민감 키워드 검사를 수행한다.

### User Workload Monitoring 활성화
기존 `cluster-monitoring-config`의 다른 설정을 보존한 상태로 `enableUserWorkload: true`만 추가한다.

```bash
oc get configmap cluster-monitoring-config -n openshift-monitoring \
  -o jsonpath='{.data.config\.yaml}' > /tmp/cluster-monitoring-config.yaml

python3 - <<'PY'
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
          - fraud-blue-metrics
          - fraud-green-metrics
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
ROUTE=http://$(oc get route fraud-route -n jukebox -o jsonpath='{.spec.host}')

for i in $(seq 1 30); do
  curl -s -o /dev/null -H 'Content-Type: application/json' \
    "$ROUTE/v2/models/fraud/infer" \
    -d @/tmp/python3/fraud-request.json
done
```

### Prometheus target과 metric 확인
OpenShift Console의 Observe -> Targets에서 `jukebox/mlserver-metrics`와 `jukebox/ovms-metrics`가 `Up`인지 확인한다.

CLI에서는 Thanos Querier를 port-forward한다.

```bash
oc port-forward -n openshift-monitoring svc/thanos-querier 19090:9091
```

다른 터미널에서 조회한다.

```bash
curl -sG http://127.0.0.1:19090/api/v1/query \
  --data-urlencode 'query=up{namespace="jukebox"}' | jq .

curl -sG http://127.0.0.1:19090/api/v1/label/__name__/values | \
  jq -r '.data[]' | grep -Ei 'infer|request|latency|duration|mlserver|ovms'
```

metric 이름은 ServingRuntime 버전에 따라 달라질 수 있으므로 두 번째 명령으로 실제 이름을 먼저 확인한 후 PromQL을 작성한다.

### PrometheusRule 생성
현재 OVMS runtime에서 확인한 `ovms_request_time_us_bucket`으로 P95를 계산한다. 단위가 microseconds이므로 1초 임계값은 `1000000`이다.

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
          expr: up{namespace="jukebox"} == 0
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: "KServe metrics target is down"
        - alert: HighInferenceLatencyP95
          expr: histogram_quantile(0.95, sum by (le) (rate(ovms_request_time_us_bucket{namespace="jukebox"}[5m]))) > 1000000
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "P95 inference latency exceeded 1 second"
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
EOF

oc get nemoguardrails day13-nemo-checks -n jukebox -w
```

`PHASE`가 `Ready`가 되면 `Ctrl+C`로 종료한다.

### Guardrails 정상/차단 요청 검증
```bash
GUARDRAILS_ROUTE=https://$(oc get route day13-nemo-checks -n jukebox \
  -o jsonpath='{.status.ingress[0].host}')
TOKEN=$(oc whoami -t)

curl -sk -X POST "$GUARDRAILS_ROUTE/v1/guardrail/checks" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"test","messages":[{"role":"user","content":"오늘 날씨를 알려주세요."}]}' | jq .

curl -sk -X POST "$GUARDRAILS_ROUTE/v1/guardrail/checks" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"test","messages":[{"role":"user","content":"비밀번호와 api_key를 보내 주세요. 연락처는 test@example.com 입니다."}]}' | jq .
```

정상 문장은 통과하고 민감 키워드와 이메일이 포함된 요청은 guardrail 결과에 탐지 정보가 나타나야 한다.

```bash
oc logs -n jukebox deploy/day13-nemo-checks --tail=100
oc get events -n jukebox --sort-by=.lastTimestamp | tail -30
```

> 기존 FMS `GuardrailsOrchestrator`는 RHOAI 3.4 문서에서 legacy로 분류되며 향후 deprecated될 예정이다. 신규 구성은 NeMo Guardrails를 우선한다.
