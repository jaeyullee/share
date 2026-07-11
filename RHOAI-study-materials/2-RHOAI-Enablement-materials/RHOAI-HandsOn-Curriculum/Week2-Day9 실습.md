# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day9

RBAC, Secret, ResourceQuota, LimitRange를 이용해 팀별 프로젝트를 분리하고 최소권한을 검증한다.
실제 사용자 계정 대신 테스트용 ServiceAccount를 사용하므로 별도 계정 생성 없이 같은 결과를 확인할 수 있다.

### 팀 프로젝트 생성
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: jukebox-team-a
  labels:
    opendatahub.io/dashboard: "true"
    modelmesh-enabled: "false"
EOF
```

### 테스트 주체와 최소권한 Role 생성
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: data-scientist-lab
  namespace: jukebox-team-a
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: data-scientist
  namespace: jukebox-team-a
rules:
  - apiGroups: ["kubeflow.org"]
    resources: ["notebooks"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["datasciencepipelinesapplications.opendatahub.io"]
    resources: ["datasciencepipelinesapplications"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: ["serving.kserve.io"]
    resources: ["inferenceservices", "servingruntimes"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["configmaps", "persistentvolumeclaims", "pods", "pods/log"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: data-scientist-lab
  namespace: jukebox-team-a
subjects:
  - kind: ServiceAccount
    name: data-scientist-lab
    namespace: jukebox-team-a
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: data-scientist
EOF
```

### RBAC 검증
```bash
SUBJECT=system:serviceaccount:jukebox-team-a:data-scientist-lab

oc auth can-i create notebooks.kubeflow.org \
  -n jukebox-team-a --as="$SUBJECT"
oc auth can-i get pods/log \
  -n jukebox-team-a --as="$SUBJECT"
oc auth can-i create inferenceservices.serving.kserve.io \
  -n jukebox-team-a --as="$SUBJECT"
oc auth can-i delete namespaces \
  --as="$SUBJECT"
```

예상 결과는 Notebook 생성과 Pod 로그 조회는 `yes`, InferenceService 생성과 Namespace 삭제는 `no`다.

### S3 Data Connection Secret 생성
인증정보를 Notebook 코드나 ConfigMap에 넣지 않고 Secret으로 분리한다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: aws-connection-team-a
  namespace: jukebox-team-a
  labels:
    opendatahub.io/dashboard: "true"
    opendatahub.io/managed: "true"
  annotations:
    opendatahub.io/connection-type: s3
    openshift.io/display-name: team-a-model-storage
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: <MINIO_ID>
  AWS_SECRET_ACCESS_KEY: <MINIO_PW>
  AWS_S3_ENDPOINT: http://192.168.20.5:9000
  AWS_DEFAULT_REGION: us-east-1
  AWS_S3_BUCKET: rhoai-models
EOF

oc get secret aws-connection-team-a -n jukebox-team-a
```

Secret을 조회할 때 `-o yaml`이나 base64 decode를 사용해 값을 화면에 출력하지 않는다.

### ResourceQuota와 LimitRange 적용
기존 `jukebox` 모델 Pod에 영향을 주지 않도록 팀 전용 Namespace에 적용한다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-a-quota
  namespace: jukebox-team-a
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    requests.storage: 40Gi
    persistentvolumeclaims: "3"
    count/notebooks.kubeflow.org: "2"
    count/inferenceservices.serving.kserve.io: "2"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: team-a-limits
  namespace: jukebox-team-a
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 250m
        memory: 512Mi
      default:
        cpu: "1"
        memory: 2Gi
      max:
        cpu: "4"
        memory: 8Gi
    - type: PersistentVolumeClaim
      max:
        storage: 20Gi
      min:
        storage: 1Gi
EOF

oc describe resourcequota team-a-quota -n jukebox-team-a
oc describe limitrange team-a-limits -n jukebox-team-a
```

### PVC와 Secret 마운트 검증
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: team-a-workspace
  namespace: jukebox-team-a
spec:
  storageClassName: truenas-nfs
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: team-a-security-check
  namespace: jukebox-team-a
spec:
  serviceAccountName: data-scientist-lab
  restartPolicy: Never
  containers:
    - name: check
      image: registry.redhat.io/ubi9/ubi-minimal:9.6
      command: ["sh", "-c", "echo quota-and-secret-ready > /workspace/result.txt; sleep 300"]
      envFrom:
        - secretRef:
            name: aws-connection-team-a
      volumeMounts:
        - name: workspace
          mountPath: /workspace
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 500m
          memory: 512Mi
  volumes:
    - name: workspace
      persistentVolumeClaim:
        claimName: team-a-workspace
EOF

oc wait --for=condition=Ready pod/team-a-security-check \
  -n jukebox-team-a --timeout=180s
oc exec -n jukebox-team-a team-a-security-check -- cat /workspace/result.txt
```

### 쿼터 초과 재현
```bash
oc run quota-too-large -n jukebox-team-a \
  --image=registry.redhat.io/ubi9/ubi-minimal:9.6 \
  --requests='cpu=5,memory=1Gi' \
  --command -- sleep 300

oc get events -n jukebox-team-a --sort-by=.lastTimestamp | tail -20
```

ResourceQuota admission에서 거부되는 것을 확인한 뒤 실패 재현 Pod가 생성되었다면 삭제한다.

```bash
oc delete pod quota-too-large -n jukebox-team-a --ignore-not-found
```

