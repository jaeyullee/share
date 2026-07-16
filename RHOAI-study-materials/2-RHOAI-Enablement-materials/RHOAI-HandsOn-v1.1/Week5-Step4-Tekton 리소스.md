# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 4 Tekton 리소스 적용

> 사전 활성화: [Week5 Step 4](<Week5-Step4 실습.md>)의 Argo CD Application 생성까지 완료한다.

외부 `week5-llm-mlops-tekton.yaml` 파일 없이 Week5 CI, promotion, Gitea trigger 리소스를 생성한다. 아래 블록 전체를 한 번에 실행한다.

```bash
WEBHOOK_AUTH="Bearer $(openssl rand -hex 32)"
oc create secret generic week5-gitea-webhook-token \
  -n rhoai-llm-mlops \
  --from-literal=authorization="$WEBHOOK_AUTH" \
  --dry-run=client -o yaml | oc apply -f -
unset WEBHOOK_AUTH

oc apply -f - <<'WEEK5_TEKTON_EOF'
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: week5-llm-ci
  namespace: rhoai-llm-mlops
spec:
  params:
    - name: source-url
      type: string
      default: https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-source.git
    - name: source-revision
      type: string
      default: main
    - name: gitops-url
      type: string
      default: https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-gitops.git
    - name: runtime-image-repo
      type: string
      default: 192.168.10.50:5010/rhoai-training/llm-lora-runtime
    - name: buildah-image
      type: string
      default: registry.redhat.io/rhel9/buildah@sha256:2347646db766dad7d85dfa9226e185e1d4de5defe26e28f4e7ca0d09b19e1bef
  workspaces:
    - name: shared
    - name: git-credentials
  tasks:
    - name: clone-and-validate
      params:
        - name: source-url
          value: $(params.source-url)
        - name: source-revision
          value: $(params.source-revision)
      workspaces:
        - name: shared
          workspace: shared
        - name: git-credentials
          workspace: git-credentials
      taskSpec:
        params:
          - {name: source-url, type: string}
          - {name: source-revision, type: string}
        workspaces:
          - {name: shared}
          - {name: git-credentials}
        results:
          - {name: commit}
        steps:
          - name: clone
            image: registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:19e62e604a6b74ded1c5df88112e5be44424fb1752df46dc1587447fe024865f
            script: |
              #!/usr/bin/env bash
              set -euo pipefail
              rm -rf "$(workspaces.shared.path)/source"
              cat > /tmp/git-askpass <<'EOF'
              #!/usr/bin/env bash
              case "$1" in
                *Username*) cat "$(workspaces.git-credentials.path)/username" ;;
                *) cat "$(workspaces.git-credentials.path)/password" ;;
              esac
              EOF
              chmod 0700 /tmp/git-askpass
              export GIT_ASKPASS=/tmp/git-askpass GIT_TERMINAL_PROMPT=0
              git -c http.sslVerify=false clone "$(params.source-url)" \
                "$(workspaces.shared.path)/source"
              cd "$(workspaces.shared.path)/source"
              git checkout "$(params.source-revision)"
              COMMIT="$(git rev-parse HEAD)"
              printf '%s' "$COMMIT" | tee "$(results.commit.path)"
              printf '\n'
              python -m py_compile models/llm-mlops/*.py
              python models/llm-mlops/validate_dataset.py \
                datasets/llm-support-sft/train.jsonl
    - name: build-runtime
      runAfter: [clone-and-validate]
      params:
        - name: image-repo
          value: $(params.runtime-image-repo)
        - name: commit
          value: $(tasks.clone-and-validate.results.commit)
        - name: buildah-image
          value: $(params.buildah-image)
      workspaces:
        - name: shared
          workspace: shared
      taskSpec:
        params:
          - {name: image-repo, type: string}
          - {name: commit, type: string}
          - {name: buildah-image, type: string}
        workspaces:
          - {name: shared}
        results:
          - {name: image-url}
          - {name: image-digest}
        steps:
          - name: build-and-push
            image: $(params.buildah-image)
            securityContext:
              privileged: true
            env:
              - name: MIRROR_REGISTRY_ID
                valueFrom:
                  secretKeyRef: {name: mirror-registry-pull, key: username}
              - name: MIRROR_REGISTRY_PW
                valueFrom:
                  secretKeyRef: {name: mirror-registry-pull, key: password}
              - name: REGISTRY_ID
                valueFrom:
                  secretKeyRef: {name: model-registry-push, key: username}
              - name: REGISTRY_PW
                valueFrom:
                  secretKeyRef: {name: model-registry-push, key: password}
            script: |
              #!/usr/bin/env bash
              set -euo pipefail
              export HOME=/tmp/buildah-home
              mkdir -p "$HOME"
              SHORT_COMMIT="$(printf '%s' '$(params.commit)' | cut -c1-12)"
              IMAGE="$(params.image-repo):${SHORT_COMMIT}"
              REPOSITORY="${IMAGE#*/}"
              MANIFEST_URL="https://192.168.10.50:5010/v2/${REPOSITORY%:*}/manifests/${SHORT_COMMIT}"
              buildah login --tls-verify=false \
                -u "$MIRROR_REGISTRY_ID" -p "$MIRROR_REGISTRY_PW" \
                192.168.10.50:5000
              buildah login --tls-verify=false -u "$REGISTRY_ID" -p "$REGISTRY_PW" \
                192.168.10.50:5010
              if curl -fsSk -u "$REGISTRY_ID:$REGISTRY_PW" \
                -D /tmp/image-headers -o /dev/null \
                -H 'Accept: application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json' \
                "$MANIFEST_URL"; then
                awk -F': ' 'tolower($1) == "docker-content-digest" {
                  gsub("\\r", "", $2); print $2
                }' /tmp/image-headers > /tmp/image-digest
                test -s /tmp/image-digest
                echo "Reusing immutable commit image: $IMAGE"
              else
                cd "$(workspaces.shared.path)/source/models/llm-mlops"
                buildah bud --storage-driver=vfs --tls-verify=false \
                  -f Containerfile -t "$IMAGE" .
                buildah push --storage-driver=vfs --tls-verify=false \
                  --digestfile /tmp/image-digest "$IMAGE" "docker://$IMAGE"
              fi
              printf '%s' "$IMAGE" | tee "$(results.image-url.path)"
              tr -d '\n' < /tmp/image-digest | tee "$(results.image-digest.path)"
    - name: compile-native-pipeline
      runAfter: [build-runtime]
      params:
        - name: commit
          value: $(tasks.clone-and-validate.results.commit)
        - name: image-url
          value: $(tasks.build-runtime.results.image-url)
        - name: image-digest
          value: $(tasks.build-runtime.results.image-digest)
      workspaces:
        - name: shared
          workspace: shared
      taskSpec:
        params:
          - {name: commit, type: string}
          - {name: image-url, type: string}
          - {name: image-digest, type: string}
        workspaces:
          - {name: shared}
        steps:
          - name: compile
            image: registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:19e62e604a6b74ded1c5df88112e5be44424fb1752df46dc1587447fe024865f
            script: |
              #!/usr/bin/env bash
              set -euo pipefail
              SHORT_COMMIT="$(printf '%s' '$(params.commit)' | cut -c1-12)"
              export RUNTIME_IMAGE="$(params.image-url)@$(params.image-digest)"
              OUT="$(workspaces.shared.path)/compiled"
              rm -rf "$OUT" && mkdir -p "$OUT/pipelines"
              python "$(workspaces.shared.path)/source/models/llm-mlops/pipeline.py" \
                --version "$SHORT_COMMIT" \
                --output "$OUT/pipelines/support-assistant-${SHORT_COMMIT}.yaml"
              cat > "$OUT/pipelines/kustomization.yaml" <<EOF
              apiVersion: kustomize.config.k8s.io/v1beta1
              kind: Kustomization
              resources:
                - support-assistant-${SHORT_COMMIT}.yaml
              EOF
    - name: push-gitops
      runAfter: [compile-native-pipeline]
      params:
        - name: gitops-url
          value: $(params.gitops-url)
        - name: commit
          value: $(tasks.clone-and-validate.results.commit)
      workspaces:
        - name: shared
          workspace: shared
        - name: git-credentials
          workspace: git-credentials
      taskSpec:
        params:
          - {name: gitops-url, type: string}
          - {name: commit, type: string}
        workspaces:
          - {name: shared}
          - {name: git-credentials}
        steps:
          - name: commit
            image: registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:19e62e604a6b74ded1c5df88112e5be44424fb1752df46dc1587447fe024865f
            script: |
              #!/usr/bin/env bash
              set -euo pipefail
              rm -rf "$(workspaces.shared.path)/gitops"
              cat > /tmp/git-askpass <<'EOF'
              #!/usr/bin/env bash
              case "$1" in
                *Username*) cat "$(workspaces.git-credentials.path)/username" ;;
                *) cat "$(workspaces.git-credentials.path)/password" ;;
              esac
              EOF
              chmod 0700 /tmp/git-askpass
              export GIT_ASKPASS=/tmp/git-askpass GIT_TERMINAL_PROMPT=0
              git -c http.sslVerify=false clone "$(params.gitops-url)" \
                "$(workspaces.shared.path)/gitops"
              cd "$(workspaces.shared.path)/gitops"
              rm -rf pipelines
              cp -a "$(workspaces.shared.path)/compiled/pipelines" .
              git config user.name week5-llm-ci
              git config user.email week5-llm-ci@example.invalid
              git add pipelines
              git diff --cached --quiet && exit 0
              git commit -m "Publish KFP pipeline $(params.commit)"
              git -c http.sslVerify=false push origin HEAD:main
    - name: start-kfp-run
      runAfter: [push-gitops]
      params:
        - name: commit
          value: $(tasks.clone-and-validate.results.commit)
        - name: image-url
          value: $(tasks.build-runtime.results.image-url)
        - name: image-digest
          value: $(tasks.build-runtime.results.image-digest)
      taskSpec:
        params:
          - {name: commit, type: string}
          - {name: image-url, type: string}
          - {name: image-digest, type: string}
        volumes:
          - name: service-ca
            configMap: {name: openshift-service-ca.crt}
        steps:
          - name: wait-and-run
            image: registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:19e62e604a6b74ded1c5df88112e5be44424fb1752df46dc1587447fe024865f
            volumeMounts:
              - {name: service-ca, mountPath: /etc/pki/week5-ca, readOnly: true}
            env:
              - {name: COMMIT, value: $(params.commit)}
              - {name: IMAGE_URL, value: $(params.image-url)}
              - {name: IMAGE_DIGEST, value: $(params.image-digest)}
            script: |
              #!/usr/bin/env python
              import os, time
              from kfp import Client

              short = os.environ["COMMIT"][:12]
              client = Client(
                  host="https://ds-pipeline-dspa.rhoai-llm-mlops.svc:8888",
                  namespace="rhoai-llm-mlops",
                  ssl_ca_cert="/etc/pki/week5-ca/service-ca.crt",
                  verify_ssl=True,
              )
              pipeline = version = None
              for _ in range(60):
                  pipelines = client.list_pipelines(page_size=100, namespace="rhoai-llm-mlops")
                  pipeline = next(
                      (p for p in (pipelines.pipelines or [])
                       if p.display_name == "Support Assistant LoRA"), None)
                  if pipeline:
                      versions = client.list_pipeline_versions(
                          pipeline_id=pipeline.pipeline_id, page_size=100)
                      version = next(
                          (v for v in (versions.pipeline_versions or [])
                           if v.display_name == f"Support Assistant LoRA {short}"), None)
                  if version:
                      break
                  time.sleep(10)
              if not pipeline or not version:
                  raise RuntimeError("Argo CD did not publish the KFP version in time")
              experiment = client.create_experiment(
                  name="week5-llm-ci", namespace="rhoai-llm-mlops")
              run = client.run_pipeline(
                  experiment_id=experiment.experiment_id,
                  job_name=f"support-assistant-{short}",
                  pipeline_id=pipeline.pipeline_id,
                  version_id=version.pipeline_version_id,
                  params={
                      "run_id": short,
                      "git_commit": os.environ["COMMIT"],
                      "training_image": f'{os.environ["IMAGE_URL"]}@{os.environ["IMAGE_DIGEST"]}',
                  },
              )
              print(run)
---
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: week5-llm-promote
  namespace: rhoai-llm-mlops
spec:
  params:
    - {name: version-name, type: string}
    - {name: model-uri, type: string}
    - {name: max-train-loss, type: string, default: "5.0"}
    - name: gitops-url
      type: string
      default: https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-gitops.git
    - {name: environment, type: string, default: staging}
  workspaces:
    - {name: shared}
    - {name: git-credentials}
  tasks:
    - name: verify-and-update-git
      workspaces:
        - {name: shared, workspace: shared}
        - {name: git-credentials, workspace: git-credentials}
      taskSpec:
        workspaces:
          - {name: shared}
          - {name: git-credentials}
        steps:
          - name: promote
            image: registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:19e62e604a6b74ded1c5df88112e5be44424fb1752df46dc1587447fe024865f
            env:
              - {name: VERSION_NAME, value: $(params.version-name)}
              - {name: MODEL_URI, value: $(params.model-uri)}
              - {name: MAX_TRAIN_LOSS, value: $(params.max-train-loss)}
              - {name: GITOPS_URL, value: $(params.gitops-url)}
              - {name: ENVIRONMENT, value: $(params.environment)}
            script: |
              #!/usr/bin/env bash
              set -euo pipefail
              python - <<'PY'
              import os, requests
              base = "http://jukebox-registry.rhoai-model-registries.svc:8080/api/model_registry/v1alpha3"
              versions = requests.get(base + "/model_versions", timeout=30).json()["items"]
              version = next(v for v in versions if v["name"] == os.environ["VERSION_NAME"])
              props = version.get("customProperties", {})
              stage = props.get("stage", {}).get("string_value")
              loss = float(props.get("train_loss", {}).get("double_value"))
              expected = "Staging" if os.environ["ENVIRONMENT"] == "staging" else "Production"
              if stage != expected or loss > float(os.environ["MAX_TRAIN_LOSS"]):
                  raise SystemExit(
                      f"promotion denied: expected={expected} stage={stage} train_loss={loss}")
              print(f"promotion gate passed: stage={stage} train_loss={loss}")
              PY
              rm -rf "$(workspaces.shared.path)/gitops"
              cat > /tmp/git-askpass <<'EOF'
              #!/usr/bin/env bash
              case "$1" in
                *Username*) cat "$(workspaces.git-credentials.path)/username" ;;
                *) cat "$(workspaces.git-credentials.path)/password" ;;
              esac
              EOF
              chmod 0700 /tmp/git-askpass
              export GIT_ASKPASS=/tmp/git-askpass GIT_TERMINAL_PROMPT=0
              git -c http.sslVerify=false clone "$GITOPS_URL" \
                "$(workspaces.shared.path)/gitops"
              cd "$(workspaces.shared.path)/gitops"
              FILE="environments/$ENVIRONMENT/inferenceservice.json"
              python - "$FILE" <<'PY'
              import json, os, sys
              path = sys.argv[1]
              doc = json.load(open(path, encoding="utf-8"))
              doc["metadata"].setdefault("annotations", {})[
                  "mlops.opendatahub.io/model-version"] = os.environ["VERSION_NAME"]
              doc["spec"]["predictor"]["model"]["storageUri"] = os.environ["MODEL_URI"]
              with open(path, "w", encoding="utf-8") as stream:
                  json.dump(doc, stream, indent=2)
                  stream.write("\n")
              PY
              KUSTOMIZATION="environments/$ENVIRONMENT/kustomization.yaml"
              grep -q 'inferenceservice.json' "$KUSTOMIZATION" || \
                printf '  - inferenceservice.json\n' >> "$KUSTOMIZATION"
              git config user.name week5-llm-promote
              git config user.email week5-llm-promote@example.invalid
              git add "$FILE" "$KUSTOMIZATION"
              git commit -m "Promote ${VERSION_NAME} to ${ENVIRONMENT}"
              git -c http.sslVerify=false push origin HEAD:main
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-week5-start-kfp-run
  namespace: rhoai-llm-mlops
spec:
  podSelector:
    matchLabels:
      app: ds-pipeline-dspa
      component: data-science-pipelines
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              tekton.dev/pipeline: week5-llm-ci
              tekton.dev/pipelineTask: start-kfp-run
      ports:
        - protocol: TCP
          port: 8888
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: week5-argocd-kfp-finalizers
  namespace: rhoai-llm-mlops
rules:
  - apiGroups: ["pipelines.kubeflow.org"]
    resources: ["pipelines/finalizers"]
    verbs: ["update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: week5-argocd-kfp-finalizers
  namespace: rhoai-llm-mlops
subjects:
  - kind: ServiceAccount
    name: openshift-gitops-argocd-application-controller
    namespace: openshift-gitops
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: week5-argocd-kfp-finalizers
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: week5-gitea-webhook-secret-reader
  namespace: rhoai-llm-mlops
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["week5-gitea-webhook-token"]
    verbs: ["get"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "patch", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: week5-gitea-webhook-secret-reader
  namespace: rhoai-llm-mlops
subjects:
  - kind: ServiceAccount
    name: llm-webhook
    namespace: rhoai-llm-mlops
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: week5-gitea-webhook-secret-reader
---
apiVersion: triggers.tekton.dev/v1beta1
kind: TriggerBinding
metadata:
  name: week5-gitea-push
  namespace: rhoai-llm-mlops
spec:
  params:
    - {name: source-url, value: $(body.repository.clone_url)}
    - {name: source-revision, value: $(body.after)}
---
apiVersion: triggers.tekton.dev/v1beta1
kind: TriggerTemplate
metadata:
  name: week5-llm-ci
  namespace: rhoai-llm-mlops
spec:
  params:
    - {name: source-url}
    - {name: source-revision}
  resourcetemplates:
    - apiVersion: tekton.dev/v1
      kind: PipelineRun
      metadata:
        generateName: week5-llm-ci-
      spec:
        pipelineRef: {name: week5-llm-ci}
        taskRunTemplate:
          serviceAccountName: llm-ci
        taskRunSpecs:
          - pipelineTaskName: build-runtime
            serviceAccountName: llm-build
        params:
          - {name: source-url, value: $(tt.params.source-url)}
          - {name: source-revision, value: $(tt.params.source-revision)}
        workspaces:
          - name: shared
            volumeClaimTemplate:
              spec:
                storageClassName: truenas-nfs
                accessModes: [ReadWriteOnce]
                resources: {requests: {storage: 5Gi}}
          - name: git-credentials
            secret: {secretName: gitea-credentials}
---
apiVersion: triggers.tekton.dev/v1beta1
kind: EventListener
metadata:
  name: week5-gitea
  namespace: rhoai-llm-mlops
spec:
  serviceAccountName: llm-webhook
  triggers:
    - name: main-push
      interceptors:
        - ref: {name: cel}
          params:
            - name: filter
              value: >-
                header.canonical('Authorization').compareSecret(
                  'authorization', 'week5-gitea-webhook-token') &&
                header.canonical('X-Gitea-Event') == 'push' &&
                body.ref == 'refs/heads/main'
      bindings:
        - ref: week5-gitea-push
      template:
        ref: week5-llm-ci
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: week5-gitea-webhook
  namespace: rhoai-llm-mlops
spec:
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
  port:
    targetPort: http-listener
  to:
    kind: Service
    name: el-week5-gitea
    weight: 100
  wildcardPolicy: None
WEEK5_TEKTON_EOF
```

다음 리소스가 생성되면 원래 Step 4로 돌아간다.

```bash
oc get pipelines.tekton.dev -n rhoai-llm-mlops
oc get eventlistener,triggerbinding,triggertemplate \
  -n rhoai-llm-mlops
oc get route week5-gitea-webhook -n rhoai-llm-mlops
oc get networkpolicy allow-week5-start-kfp-run \
  -n rhoai-llm-mlops
oc auth can-i update pipelines/finalizers.pipelines.kubeflow.org \
  -n rhoai-llm-mlops \
  --as=system:serviceaccount:openshift-gitops:openshift-gitops-argocd-application-controller
oc auth can-i get secret/week5-gitea-webhook-token \
  -n rhoai-llm-mlops \
  --as=system:serviceaccount:rhoai-llm-mlops:llm-webhook
```

RHOAI의 KFP도 `Pipeline`이라는 이름의 CRD를 제공하므로 `oc get pipeline`은 `pipelines.pipelines.kubeflow.org`로 해석될 수 있다. Tekton Pipeline을 조회할 때는 `pipelines.tekton.dev`처럼 API group까지 지정한다.

DSPA가 생성한 기본 NetworkPolicy는 KFP component와 Workbench Pod만 API 포트 `8888`에 접근하도록 허용한다. 별도 설치한 Tekton은 자동 허용 대상이 아니므로 위 정책은 `week5-llm-ci`의 `start-kfp-run` Task Pod만 DSPA API에 추가로 연결한다. Operator가 관리하는 `ds-pipelines-dspa` 정책은 직접 수정하지 않는다.

KFP API는 `PipelineVersion` 생성 시 상위 `Pipeline`을 가리키는 `blockOwnerDeletion` owner reference를 자동으로 추가한다. Kubernetes는 이를 허용하기 전에 요청 주체가 `pipelines/finalizers`를 갱신할 수 있는지 별도로 검사하므로, namespace 관리용 Argo CD 기본 Role의 일반 `pipelines` 권한만으로는 부족하다. 위 별도 Role은 Argo CD application controller에 이 subresource의 `update`만 추가하며 Operator가 관리하는 기본 Role은 수정하지 않는다.

`build-runtime`은 source commit의 앞 12자를 image tag로 사용한다. KFP `PipelineVersion`의 pipeline spec은 생성 후 변경할 수 없으므로 같은 commit을 재실행할 때 이미 존재하는 tag를 다시 빌드하거나 덮어쓰지 않고 registry manifest의 기존 digest를 재사용한다. 의존성이나 Containerfile을 바꿔 새 이미지를 만들어야 하면 source commit도 새로 생성한다.

EventListener의 CEL interceptor는 `Authorization` header를 Secret과 상수 시간 비교한 뒤 Gitea push와 `main` branch 조건을 검사한다. 실제 토큰은 Kubernetes Secret과 Git server 설정에만 저장하고 문서나 Git 저장소에 기록하지 않는다.
