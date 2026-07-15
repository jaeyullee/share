# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 3 Source와 GitOps 저장소 준비

> 사전 활성화: [Week5 Step 2](<Week5-Step2 실습.md>)를 완료하고 Gitea에 저장소를 만들 수 있어야 한다.

소스와 배포 선언을 서로 다른 저장소로 분리한다. Tekton은 source repository를 읽고 GitOps repository만 갱신하며 클러스터에 InferenceService를 직접 적용하지 않는다.

### Gitea 저장소 생성

Gitea에서 다음 비공개 저장소를 만든다.

| 저장소 | 용도 |
|---|---|
| `hands-on/week5-llm-source` | dataset, 훈련 코드, Containerfile, KFP DSL |
| `hands-on/week5-llm-gitops` | KFP CR과 staging/production serving 선언 |

PAT에는 두 저장소를 읽고 쓸 최소 권한만 부여한다.

### Source repository 작성

```bash
rm -rf /tmp/week5-llm-source
mkdir -p /tmp/week5-llm-source/models \
  /tmp/week5-llm-source/datasets

cp -a /tmp/python3/models/llm-mlops \
  /tmp/week5-llm-source/models/
cp -a /tmp/python3/datasets/llm-support-sft \
  /tmp/week5-llm-source/datasets/

cd /tmp/week5-llm-source
python -m py_compile models/llm-mlops/*.py
python models/llm-mlops/validate_dataset.py \
  datasets/llm-support-sft/train.jsonl

git init
git add .
git commit -m 'Add Week 5 LLM MLOps source'
git branch -M main
git remote add origin \
  https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-source.git
git push -u origin main
```

Git remote URL에 ID나 PAT를 포함하지 않는다. credential prompt에 입력하거나 credential helper를 사용한다.

### GitOps repository skeleton 작성

```bash
rm -rf /tmp/week5-llm-gitops /tmp/week5-serving-rendered.yaml
mkdir -p /tmp/week5-llm-gitops/pipelines \
  /tmp/week5-llm-gitops/environments/staging \
  /tmp/week5-llm-gitops/environments/production

cat > /tmp/week5-llm-gitops/pipelines/kustomization.yaml <<'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: []
EOF
```

serving template를 환경별 JSON으로 렌더링한다. 초기 Kustomization에는 ServingRuntime만 넣고 InferenceService는 promotion Pipeline이 gate 통과 후 추가한다.

```bash
for ENV in staging production; do
  if [ "$ENV" = staging ]; then
    NS=rhoai-llm-staging
    STAGE=Staging
  else
    NS=rhoai-llm-production
    STAGE=Production
  fi

  sed \
    -e "s/<TARGET_NAMESPACE>/$NS/g" \
    -e "s/<TARGET_ENVIRONMENT>/$ENV/g" \
    -e "s/<TARGET_STAGE>/$STAGE/g" \
    -e 's/<RUN_ID>/not-promoted/g' \
    /tmp/python3/manifests/week5-llm-mlops-serving.yaml \
    > /tmp/week5-serving-rendered.yaml

  oc create --dry-run=client \
    -f /tmp/week5-serving-rendered.yaml -o json | \
    jq '.items[] | select(.kind == "ServingRuntime")' \
    > "/tmp/week5-llm-gitops/environments/$ENV/runtime.json"

  oc create --dry-run=client \
    -f /tmp/week5-serving-rendered.yaml -o json | \
    jq '.items[] | select(.kind == "InferenceService")' \
    > "/tmp/week5-llm-gitops/environments/$ENV/inferenceservice.json"

  cat > "/tmp/week5-llm-gitops/environments/$ENV/kustomization.yaml" <<'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - runtime.json
EOF
done

rm -f /tmp/week5-serving-rendered.yaml
oc kustomize /tmp/week5-llm-gitops/environments/staging >/dev/null
oc kustomize /tmp/week5-llm-gitops/environments/production >/dev/null
```

### GitOps 저장소 push

```bash
cd /tmp/week5-llm-gitops
git init
git add .
git commit -m 'Initialize Week 5 GitOps repository'
git branch -M main
git remote add origin \
  https://gitea.apps.sno.ocp422.com/hands-on/week5-llm-gitops.git
git push -u origin main
```

### 확인 기준

- source repository에는 Secret이나 실제 ID/PW가 없다.
- GitOps repository에는 `pipelines`, `environments/staging`, `environments/production`이 있다.
- 두 환경의 초기 Kustomization은 runtime만 렌더링한다.
- `inferenceservice.json`은 저장되어 있지만 promotion 전에는 Argo CD 적용 대상이 아니다.
