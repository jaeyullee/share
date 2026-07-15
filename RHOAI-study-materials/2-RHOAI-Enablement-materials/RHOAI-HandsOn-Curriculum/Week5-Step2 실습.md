# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 2 OpenShift Pipelines와 프로젝트 구성

> 사전 활성화: [Week5 Step 1](Week5-Step1%20실습.md)의 artifact 준비와 [Week1 Day1&2](Week1-Day1%262-환경구성.md#tekton-cicd와-argo-cd-gitops-구성)의 GitOps 구성을 완료한다.

OpenShift Pipelines Operator를 설치하고 LLM CI, KFP, Trainer, staging과 production을 분리한 Namespace를 만든다.

### OpenShift Pipelines 설치

```bash
oc get operatorgroup -n openshift-operators
```

기존 `global-operators` OperatorGroup이 있으면 그대로 사용한다. 같은 Namespace에 OperatorGroup을 추가로 만들지 않는다. OperatorGroup이 전혀 없는 새 클러스터에서만 OLM 설계에 맞는 OperatorGroup을 먼저 생성한다.

```bash
oc apply -f - <<'EOF'
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: openshift-pipelines-operator-rh
  namespace: openshift-operators
spec:
  channel: latest
  installPlanApproval: Automatic
  name: openshift-pipelines-operator-rh
  source: cs-redhat-operator-index-v4-22
  sourceNamespace: openshift-marketplace
EOF

oc get csv -n openshift-operators | grep openshift-pipelines
oc get tektonconfig config
oc get pods -n openshift-pipelines
```

CSV가 `Succeeded`이고 TektonConfig가 Ready가 될 때까지 기다린다.

CI의 Buildah task는 이 Operator package `relatedImages`에 포함된 digest를 사용한다. 폐쇄망 mirror에 같은 digest가 있는지 확인한다.

```bash
oc run week5-buildah-check -n rhoai-llm-mlops \
  --rm -i --restart=Never --pod-running-timeout=180s \
  --image=registry.redhat.io/rhel9/buildah@sha256:2347646db766dad7d85dfa9226e185e1d4de5defe26e28f4e7ca0d09b19e1bef \
  --command -- sh -c \
  'export HOME=/tmp/buildah-home; mkdir -p "$HOME"; buildah --version'
```

`buildah version 1.43.1`과 같이 출력돼야 한다. `ImagePullBackOff`이면 OpenShift Pipelines Operator의 현재 CSV `relatedImages`를 mirror에 추가한 뒤 진행한다. tag가 아니라 설치할 Operator 버전이 참조하는 digest를 사용해야 한다.

### Namespace와 RBAC 적용

```bash
oc apply -f \
  /tmp/python3/manifests/week5-llm-mlops-platform.yaml

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
oc apply -f \
  /tmp/python3/manifests/week5-llm-mlops-dspa.yaml

oc get dspa dspa -n rhoai-llm-mlops -w
```

`READY=True`가 되면 `Ctrl+C`로 종료한다.

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
