# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 1 - Day4 - custom servingruntime

## 커스텀 servingruntime 을 만들어서 배포하고 싶은 경우
```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: custom-runtime-skeleton
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    openshift.io/display-name: "Custom Runtime (skeleton)"
spec:
  supportedModelFormats:
    - name: custom
      version: "1"
      autoSelect: false
  protocolVersions:
    - v2
  multiModel: false
  containers:
    - name: kserve-container
      image: image-registry.openshift-image-registry.svc:5000/jukebox/my-custom-runtime:latest
      ports:
        - containerPort: 8080
      env:
        - name: MODEL_DIR
          value: /mnt/models
      resources:
        requests:
          cpu: "500m"
          memory: 1Gi
        limits:
          cpu: "2"
          memory: 2Gi
```

## Template 을 이용해서 servingruntime 을 배포하고 싶은 경우
```bash
oc get template -n redhat-ods-applications

## 예시 : MLServer
oc process mlserver-runtime-template \
  -n redhat-ods-applications \
  > mlserver-runtime.yaml

## metadata.namespace, metadata.name, image 수정
## 사용 이미지 반입 필요
oc apply -n jukebox -f mlserver-runtime.yaml

oc get servingruntime -n jukebox
oc describe servingruntime -n jukebox <runtime-name>
```

## inferenceservice 에서 servingruntime 참조 예시
```yaml
spec:
  predictor:
    model:
      runtime: <servingruntime 이름>
      modelFormat:
        name: sklearn
      storageUri: s3://<bucket 이름>/...
```

## 실습 리소스 정리
이 문서는 ServingRuntime 예시만 생성하므로 기본 절차에는 삭제할 InferenceService가 없다. 예시를 확장해 InferenceService를 생성했다면 해당 InferenceService만 삭제하고 ServingRuntime은 유지한다.

```bash
oc delete isvc <inferenceservice-name> -n jukebox \
  --ignore-not-found --wait=true --timeout=5m

oc get servingruntime -n jukebox
```
