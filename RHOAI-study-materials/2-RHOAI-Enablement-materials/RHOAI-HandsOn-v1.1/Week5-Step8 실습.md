# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 8 Production 승격, Git rollback과 정리

> 사전 활성화: [Week5 Step 7](<Week5-Step7 실습.md>)의 staging 추론 검증을 완료한다.

Model Registry에서 승인 단계를 변경한 뒤 production에 승격한다. 단일 GPU 검증 환경에서는 staging을 먼저 내리고 production을 배포한다. 마지막으로 Git rollback과 전체 실습 리소스 정리를 확인한다.

### Registry 승인 상태 변경

RHOAI 대시보드에서 `AI hub` -> `Models` -> `Registry` -> `support-assistant` -> 해당 Model Version으로 이동한다.

1. staging 추론 결과와 `train_loss`, source commit, S3 URI를 다시 확인한다.
2. custom property `stage`를 `Staging`에서 `Production`으로 변경한다.
3. Model Registry의 기본 `state=LIVE`는 그대로 둔다.

운영에서는 이 변경을 모델 승인 RBAC와 감사 가능한 approval workflow로 제한한다.

### Staging GPU 반환

GitOps 저장소의 staging 적용 목록에서 InferenceService를 제거하고 push한다.

```bash
cd /tmp/week5-llm-gitops
git pull --ff-only
sed -i '/inferenceservice.json/d' \
  environments/staging/kustomization.yaml
git add environments/staging/kustomization.yaml
git commit -m 'Stop Week 5 staging serving'
git push origin main
```

이 실습의 Argo CD Application은 첫 검증을 위해 `prune: false`이므로 Git에서 제거한 뒤 기존 ISVC는 명시적으로 삭제한다. Git에서 먼저 제거해야 self-heal이 다시 만들지 않는다.

```bash
oc delete isvc support-assistant-staging \
  -n rhoai-llm-staging --ignore-not-found

oc wait --for=delete pod \
  -l serving.kserve.io/inferenceservice=support-assistant-staging \
  -n rhoai-llm-staging --timeout=300s
```

### Production promotion

```bash
RUN_ID=<SHORT_COMMIT>
MODEL_URI="s3://rhoai-llm-mlops/models/support-assistant/$RUN_ID/model"

sed \
  -e "s/week5-promote-staging/week5-promote-production/g" \
  -e 's/value: staging/value: production/' \
  /tmp/week5-promote-staging.yaml \
  > /tmp/week5-promote-production.yaml

PROD_RUN=$(oc create -f /tmp/week5-promote-production.yaml \
  -o jsonpath='{.metadata.name}')

tkn pipelinerun logs -n rhoai-llm-mlops \
  "$PROD_RUN" -f
```

production gate는 Registry `stage=Production`을 요구한다. 성공 후 상태를 확인한다.

```bash
oc wait --for=condition=Ready \
  isvc/support-assistant-production \
  -n rhoai-llm-production --timeout=600s

oc get application week5-llm-serving-production \
  -n openshift-gitops
oc get servingruntime,isvc,pod -n rhoai-llm-production
```

### Production 추론

첫 Bastion 터미널에서 실행한다.

```bash
oc port-forward -n rhoai-llm-production \
  deploy/support-assistant-production-predictor 18091:8080
```

다른 Bastion 터미널에서 실행한다.

```bash
cd /tmp/python3
export RHOAI_HANDSON_DIR="$PWD"
curl -sS -H 'Content-Type: application/json' \
  http://127.0.0.1:18091/v1/chat/completions \
  -d @"$RHOAI_HANDSON_DIR/models/llm-mlops/inference-request.json" | \
  jq '{id,model,answer:.choices[0].message.content,usage}'
```

staging에서 검증한 version과 production ISVC annotation, S3 URI가 같은지 확인한다.

### Git rollback 검증

두 번째 모델 version이 있을 때는 production 승격 commit을 되돌려 이전 `inferenceservice.json`으로 복귀시킨다.

```bash
cd /tmp/week5-llm-gitops
git pull --ff-only
git log --oneline -- environments/production

git revert <PRODUCTION_PROMOTION_COMMIT>
git push origin main

oc get application week5-llm-serving-production \
  -n openshift-gitops -w
```

Argo CD 동기화 후 production ISVC의 model-version annotation과 storage URI가 이전 값으로 돌아오는지 확인하고 같은 추론 요청을 다시 호출한다. 첫 모델 하나만 만든 경우에는 `git revert` 원리를 확인하고 실제 rollback은 생략한다.

### 실습 리소스 정리

production ISVC를 Git 관리 목록에서 먼저 제거한다.

```bash
cd /tmp/week5-llm-gitops
sed -i '/inferenceservice.json/d' \
  environments/production/kustomization.yaml
git add environments/production/kustomization.yaml
git commit -m 'Stop Week 5 production serving'
git push origin main

oc delete isvc support-assistant-production \
  -n rhoai-llm-production --ignore-not-found
```

Week5 전용 클러스터 리소스를 제거한다. 기존 `jukebox` Model Registry, RHOAI DSC, Trainer, GitOps Operator와 GPU Operator는 삭제하지 않는다.

```bash
oc adm policy remove-scc-from-user privileged \
  -z llm-build -n rhoai-llm-mlops

oc delete application \
  week5-llm-pipelines \
  week5-llm-serving-staging \
  week5-llm-serving-production \
  -n openshift-gitops --ignore-not-found

oc delete secret week5-llm-gitops-repository \
  -n openshift-gitops --ignore-not-found

oc delete clusterrolebinding \
  week5-llm-webhook-interceptor-reader --ignore-not-found
oc delete clusterrole \
  week5-llm-webhook-interceptor-reader --ignore-not-found

oc delete namespace \
  rhoai-llm-mlops rhoai-llm-staging rhoai-llm-production \
  --ignore-not-found
```

OpenShift Pipelines를 다른 실습에서 쓰지 않고 이번 Step 2에서만 설치했다면 선택적으로 Subscription과 CSV를 제거한다. 공유 클러스터에서는 제거하지 않는다.

```bash
oc delete subscription openshift-pipelines-operator-rh \
  -n openshift-operators --ignore-not-found

CSV=$(oc get csv -n openshift-operators -o name | \
  grep openshift-pipelines-operator-rh || true)
test -z "$CSV" || oc delete -n openshift-operators "$CSV"
```

S3 산출물과 Gitea 저장소는 재검증과 이력 확인을 위해 기본적으로 보존한다. 완전 초기화가 필요할 때만 별도 확인 후 `rhoai-llm-mlops` bucket과 두 저장소를 삭제한다.

### 최종 확인

```bash
oc get namespace | grep rhoai-llm || true
oc get application -n openshift-gitops | grep week5-llm || true
oc get isvc -A | grep support-assistant || true
oc get pod -A | grep -E 'week5|support-assistant|llm-lora' || true
```

모두 빈 결과여야 한다. 기존 Day 1~15 리소스와 Operator 상태는 변경되지 않아야 한다.
