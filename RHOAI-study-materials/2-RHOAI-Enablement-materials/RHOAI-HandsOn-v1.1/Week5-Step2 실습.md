# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 2 OpenShift Pipelines와 프로젝트 구성

> **환경별 재확인**: StorageClass, registry pull/push Secret, S3 Secret과 Namespace 보안 정책은 환경마다 다르다. placeholder를 대상 환경 값으로 치환하되 실제 자격 증명은 문서에 기록하지 않는다. 공통 경계 조건은 [실습자료 검토 항목](<00-실습자료-검토항목.md#환경별-재확인>)을 참고한다.

> 사전 활성화: [Week5 Step 1](<Week5-Step1 실습.md>)의 artifact 준비와 [Week1 Day1&2](<Week1-Day1&2-환경구성.md#tekton-cicd와-argo-cd-gitops-구성>)의 GitOps 구성을 완료한다.

OpenShift Pipelines Operator를 설치하고 LLM CI, KFP, Trainer, staging과 production을 분리한 Namespace를 만든다.

### OpenShift Pipelines 설치 확인

```bash
oc get operatorgroup -n openshift-operators
oc get csv -n openshift-operators | grep openshift-pipelines
oc get tektonconfig config
oc get pods -n openshift-pipelines
```


CI의 Buildah task는 이 Operator package `relatedImages`에 포함된 digest를 사용한다. 폐쇄망 mirror에 같은 digest가 있는지 확인한다.

```bash
oc new-project rhoai-llm-mlops
oc run week5-buildah-check -n rhoai-llm-mlops \
  --rm -i --restart=Never --pod-running-timeout=180s \
  --image=registry.redhat.io/rhel9/buildah@sha256:2347646db766dad7d85dfa9226e185e1d4de5defe26e28f4e7ca0d09b19e1bef \
  --command -- sh -c \
  'export HOME=/tmp/buildah-home; mkdir -p "$HOME"; buildah --version'
oc delete project rhoai-llm-mlops
```

`buildah version 1.43.1`과 같이 출력돼야 한다. `ImagePullBackOff`이면 OpenShift Pipelines Operator의 현재 CSV `relatedImages`를 mirror에 추가한 뒤 진행한다. tag가 아니라 설치할 Operator 버전이 참조하는 digest를 사용해야 한다.

### Namespace와 RBAC 적용

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: rhoai-llm-mlops
  labels:
    opendatahub.io/dashboard: "true"
    argocd.argoproj.io/managed-by: openshift-gitops
---
apiVersion: v1
kind: Namespace
metadata:
  name: rhoai-llm-staging
  labels:
    opendatahub.io/dashboard: "true"
    argocd.argoproj.io/managed-by: openshift-gitops
---
apiVersion: v1
kind: Namespace
metadata:
  name: rhoai-llm-production
  labels:
    opendatahub.io/dashboard: "true"
    argocd.argoproj.io/managed-by: openshift-gitops
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: llm-trainer
  namespace: rhoai-llm-mlops
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: llm-ci
  namespace: rhoai-llm-mlops
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: llm-build
  namespace: rhoai-llm-mlops
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: llm-webhook
  namespace: rhoai-llm-mlops
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: llm-trainjob-manager
  namespace: rhoai-llm-mlops
rules:
  - apiGroups: [trainer.kubeflow.org]
    resources: [trainjobs]
    verbs: [create, get, list, watch, patch, delete]
  - apiGroups: [jobset.x-k8s.io]
    resources: [jobsets]
    verbs: [get, list, watch]
  - apiGroups: [""]
    resources: [pods, pods/log, events]
    verbs: [get, list, watch]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pipeline-runner-can-manage-trainjobs
  namespace: rhoai-llm-mlops
subjects:
  - kind: ServiceAccount
    name: pipeline-runner-dspa
    namespace: rhoai-llm-mlops
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: llm-trainjob-manager
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: llm-webhook-pipelinerun-creator
  namespace: rhoai-llm-mlops
rules:
  - apiGroups: [tekton.dev]
    resources: [pipelineruns]
    verbs: [create, get, list, watch]
  - apiGroups: [triggers.tekton.dev]
    resources: [eventlisteners, triggers, triggerbindings, triggertemplates, interceptors]
    verbs: [get, list, watch]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: llm-webhook-pipelinerun-creator
  namespace: rhoai-llm-mlops
subjects:
  - kind: ServiceAccount
    name: llm-webhook
    namespace: rhoai-llm-mlops
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: llm-webhook-pipelinerun-creator
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: week5-llm-webhook-interceptor-reader
rules:
  - apiGroups: [triggers.tekton.dev]
    resources: [clusterinterceptors]
    verbs: [get, list, watch]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: week5-llm-webhook-interceptor-reader
subjects:
  - kind: ServiceAccount
    name: llm-webhook
    namespace: rhoai-llm-mlops
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: week5-llm-webhook-interceptor-reader
EOF

oc adm policy add-scc-to-user privileged \
  -z llm-build -n rhoai-llm-mlops
```

`privileged` SCC는 image build task에만 필요한 권한이다. PipelineRun의 `taskRunSpecs`가 `build-runtime`만 `llm-build` ServiceAccount로 실행하고, 나머지 task는 `llm-ci`를 사용한다. 운영에서는 전용 build Namespace, rootless Buildah 또는 지원되는 cluster build service로 권한을 더 줄인다.

### 인증 Secret 생성

공개 Git 저장소에 Secret YAML을 저장하지 않는다.

```bash
oc create secret generic llm-s3 -n rhoai-llm-mlops \
  --from-literal=AWS_ACCESS_KEY_ID='<MINIO_ID>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<MINIO_PW>' \
  --from-literal=AWS_ENDPOINT_URL='http://192.168.20.5:9000' \
  --from-literal=AWS_DEFAULT_REGION='us-east-1' \
  --dry-run=client -o yaml | oc apply -f -

oc create secret docker-registry model-registry-pull \
  -n rhoai-llm-mlops \
  --docker-server=192.168.10.50:5010 \
  --docker-username='<MODEL_REGISTRY_ID>' \
  --docker-password='<MODEL_REGISTRY_PW>' \
  --dry-run=client -o yaml | oc apply -f -

oc create secret generic model-registry-push \
  -n rhoai-llm-mlops \
  --from-literal=username='<MODEL_REGISTRY_ID>' \
  --from-literal=password='<MODEL_REGISTRY_PW>' \
  --dry-run=client -o yaml | oc apply -f -

oc create secret generic mirror-registry-pull \
  -n rhoai-llm-mlops \
  --from-literal=username='<MIRROR_REGISTRY_ID>' \
  --from-literal=password='<MIRROR_REGISTRY_PW>' \
  --dry-run=client -o yaml | oc apply -f -

oc create secret generic gitea-credentials \
  -n rhoai-llm-mlops \
  --from-literal=username='<GITEA_ID>' \
  --from-literal=password='<GITEA_PAT>' \
  --dry-run=client -o yaml | oc apply -f -
```

### Serving Namespace의 S3 Secret

```bash
for NS in rhoai-llm-staging rhoai-llm-production; do
  oc create secret generic aws-connection-llm-models -n "$NS" \
    --from-literal=AWS_ACCESS_KEY_ID='<MINIO_ID>' \
    --from-literal=AWS_SECRET_ACCESS_KEY='<MINIO_PW>' \
    --from-literal=AWS_S3_ENDPOINT='http://192.168.20.5:9000' \
    --from-literal=AWS_DEFAULT_REGION='us-east-1' \
    --from-literal=AWS_S3_BUCKET='rhoai-llm-mlops' \
    --dry-run=client -o yaml | oc apply -f -

  oc label secret aws-connection-llm-models -n "$NS" \
    opendatahub.io/dashboard=true --overwrite
  oc annotate secret aws-connection-llm-models -n "$NS" \
    opendatahub.io/connection-type=s3 \
    openshift.io/display-name='Week 5 LLM models' --overwrite
done
```

### Kubernetes-native DSPA 생성

```bash
oc apply -f - <<'EOF'
apiVersion: datasciencepipelinesapplications.opendatahub.io/v1
kind: DataSciencePipelinesApplication
metadata:
  name: dspa
  namespace: rhoai-llm-mlops
spec:
  dspVersion: v2
  apiServer:
    pipelineStore: kubernetes
  database:
    mariaDB:
      deploy: true
      storageClassName: truenas-nfs
      pvcSize: 5Gi
  objectStorage:
    externalStorage:
      bucket: rhoai-llm-mlops
      host: 192.168.20.5
      port: "9000"
      scheme: http
      region: us-east-1
      s3CredentialsSecret:
        secretName: llm-s3
        accessKey: AWS_ACCESS_KEY_ID
        secretKey: AWS_SECRET_ACCESS_KEY
EOF

oc get dspa dspa -n rhoai-llm-mlops -w \
  -o custom-columns='NAME:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status,REASON:.status.conditions[?(@.type=="Ready")].reason,MESSAGE:.status.conditions[?(@.type=="Ready")].message'
```

`READY=True`, `REASON=MinimumReplicasAvailable`, `MESSAGE=All components are ready.`가 표시되면 `Ctrl+C`로 종료한다. 생성 직후에는 `False` 또는 `Unknown`이 표시될 수 있다.

```bash
oc get dspa dspa -n rhoai-llm-mlops \
  -o jsonpath='{.spec.apiServer.pipelineStore}{"\n"}'

oc auth can-i create trainjobs.trainer.kubeflow.org \
  -n rhoai-llm-mlops \
  --as=system:serviceaccount:rhoai-llm-mlops:pipeline-runner-dspa
```

예상 출력은 각각 `kubernetes`, `yes`다.

### 확인 기준

- OpenShift Pipelines CSV와 TektonConfig가 Ready다.
- 세 Namespace가 존재하고 기본 Argo CD 관리 label이 있다.
- DSPA `pipelineStore`는 `kubernetes`다.
- KFP Pipeline Runner가 TrainJob을 생성할 수 있다.
- Secret 값은 Git과 shell history용 파일에 저장하지 않았다.
