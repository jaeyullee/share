---
custom-width: 60
---
# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 2 - Day6

> 사전 활성화: [Week1 Day1&2 - 대시보드 Workbench의 Kueue 사용 여부](Week1-Day1%262-환경구성.md#대시보드-workbench의-kueue-사용-여부)를 먼저 확인한다. 이 Day의 기본 YAML 경로는 `disableKueue=true`, DSC `kueue: Removed` 모드로 실행할 수 있다.

### gitea 준비
1. gitea 설치 (helm 이용)
2. gitea 콘솔 접속 및 `<GITEA_ID>` 로그인
3. hands-on 조직 생성
4. day06 레포 생성 (비공개)
5. 액세스 토큰 발급(gitea는 personal access token 만 존재)
6. bastion에서 프로젝트 clone

### 훈련 준비 및 git push
```bash
ls /tmp/python3/models/train_iris_sklearn.py

mkdir -p /opt/rhoai-data/git-repo/hands-on
cd /opt/rhoai-data/git-repo/hands-on
GIT_SSL_NO_VERIFY=true git clone https://gitea.apps.sno.ocp422.com/hands-on/day06.git
cd day06

mkdir -p models
cp /tmp/python3/models/train_iris_sklearn.py ./models/

cat >requirements.txt <<'EOF'
scikit-learn==1.6.1
pandas==2.3.3
numpy==1.26.4
scipy==1.13.1
joblib==1.4.2
threadpoolctl==3.5.0
python-dateutil==2.9.0.post0
pytz==2025.2
tzdata==2025.2
six==1.17.0
EOF

## 워크벤치에서 pip install 시 내부 넥서스 정보로 이용
cat > pip.conf <<'EOF'
[global]
index-url = http://192.168.10.50:8081/repository/pypi-hosted/simple
trusted-host = 192.168.10.50
no-cache-dir = true
EOF

## mc cli download
curl -L https://dl.min.io/client/mc/release/linux-amd64/mc -o ./mc

git add .
git commit -m "initial workbench settings"
GIT_SSL_NO_VERIFY=true git push -u origin main

## Workbench Python 3.12용 라이브러리를 내부 Nexus에 업로드
## 베스천 Python 버전으로 wheel tag가 결정되지 않도록 대상 interpreter와 platform을 명시한다.
rm -rf /tmp/wheelhouse-cp312
mkdir -p /tmp/wheelhouse-cp312
cd /tmp

python3 -m venv /tmp/pypi-upload-venv
source /tmp/pypi-upload-venv/bin/activate
python3 -m pip install --upgrade pip

python3 -m pip download \
  --index-url https://pypi.org/simple \
  --no-cache-dir \
  --only-binary=:all: \
  --python-version 312 \
  --implementation cp \
  --abi cp312 \
  --platform manylinux_2_28_x86_64 \
  --platform manylinux_2_24_x86_64 \
  --platform manylinux_2_17_x86_64 \
  --platform manylinux2014_x86_64 \
  -r /opt/rhoai-data/git-repo/hands-on/day06/requirements.txt \
  -d /tmp/wheelhouse-cp312

## 바이너리 패키지는 cp312 wheel인지 확인한다. py2.py3-none/py3-none은 공용 wheel이다.
ls -1 /tmp/wheelhouse-cp312

python -m pip show twine pkginfo
## 설치 안됐으면 아래 진행
# python3 -m pip install \
#   'twine==5.0.0' \
#   'pkginfo==1.12.1.2'

twine upload \
  --skip-existing \
  --repository-url http://192.168.10.50:8081/repository/pypi-hosted/ \
  -u <NEXUS_ID> -p '<NEXUS_PW>' \
  /tmp/wheelhouse-cp312/*
```

베스천의 Python이 3.9인 상태에서 대상 옵션 없이 `pip download`를 실행하면 `cp39` wheel만 준비된다. Python 3.12 Workbench는 이를 호환되지 않는 파일로 제외하므로, Nexus에 패키지 이름과 버전이 존재해도 `No matching distribution found`가 발생한다.

업로드 후 `scikit-learn`의 `cp312` wheel이 인덱스에 노출되는지 확인한다.

```bash
curl -fsS \
  http://192.168.10.50:8081/repository/pypi-hosted/simple/scikit-learn/ | \
  grep cp312
```

### Workbench 생성
```bash
oc apply -f -<<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jukebox-workbench
  namespace: jukebox
EOF
oc apply -f -<<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jukebox-workbench-pvc
  namespace: jukebox
  labels:
    opendatahub.io/dashboard: "true"
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
EOF
oc apply -f -<<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: git-creds
  namespace: jukebox
type: Opaque
stringData:
  username: <GITEA_ID>
  password: <git_pat>
EOF
oc apply -f -<<'EOF'
apiVersion: kubeflow.org/v1
kind: Notebook
metadata:
  name: jukebox-workbench
  namespace: jukebox
  labels:
    app: jukebox-workbench
    opendatahub.io/dashboard: "true"
  annotations:
    openshift.io/display-name: "Jukebox Workbench"
    notebooks.opendatahub.io/inject-auth: "true"
    notebooks.opendatahub.io/last-image-selection: >-
      s2i-generic-data-science-notebook:3.4
    notebooks.opendatahub.io/last-image-version-git-commit-selection: "d3137ca"
spec:
  template:
    spec:
      serviceAccountName: jukebox-workbench
      containers:
        - name: jukebox-workbench
          image: >-
            registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:d82680de0790b333892da2179c12225f5858f862b060964f2c62314cb23714fe
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "2"
              memory: 4Gi
          env:
            - name: NOTEBOOK_ARGS
              value: |-
                --ServerApp.port=8888
                --ServerApp.token=''
                --ServerApp.password=''
                --ServerApp.base_url=/notebook/jukebox/jukebox-workbench
                --ServerApp.quit_button=False
            - name: JUPYTER_IMAGE
              value: >-
                registry.redhat.io/rhoai/odh-workbench-jupyter-datascience-cpu-py312-rhel9@sha256:d82680de0790b333892da2179c12225f5858f862b060964f2c62314cb23714fe
            - name: GIT_USERNAME
              valueFrom:
                secretKeyRef:
                  name: git-creds
                  key: username
            - name: GIT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: git-creds
                  key: password
          volumeMounts:
            - name: jukebox-workbench-pvc
              mountPath: /opt/app-root/src
          ports:
            - containerPort: 8888
              name: notebook-port
              protocol: TCP
      volumes:
        - name: jukebox-workbench-pvc
          persistentVolumeClaim:
            claimName: jukebox-workbench-pvc
EOF
```

>Notebook의 `image`는 노드의 CRI가 직접 pull한다. 따라서 노드 DNS에서 해석할 수 없는 `image-registry.openshift-image-registry.svc:5000/...`를 쓰지 않고, RHOAI ImageStream의 원본 digest를 사용해 IDMS가 내부 mirror로 치환하도록 한다. RHOAI 버전이 바뀌면 다음 명령으로 현재 source image를 다시 확인한다.
```bash
oc get imagestream -n redhat-ods-applications -o yaml | \
  grep -A8 odh-workbench-jupyter-datascience
```

> notebooks.opendatahub.io/last-image-version-git-commit-selection: "d3137ca" 는 RHOAI 버전이 바뀌면 다음 명령으로 현재 source image digest를 다시 확인한다. 해당 annotaion이 없으면 deprecated로 판정합니다.
```
oc get imagestream s2i-generic-data-science-notebook \
  -n redhat-ods-applications \
  -o jsonpath='{.spec.tags[?(@.name=="3.4")].annotations.opendatahub\.io/notebook-build-commit}{"\n"}'
```
### 모델 생성&배포
1. Workbench 접속
```bash
## git clone
cd /opt/app-root/src
git clone http://${GIT_USERNAME}:${GIT_TOKEN}@gitea-http.gitea.svc.cluster.local:3000/hands-on/day06.git
cd day06

## 내부 nexus 이용해서 모델 생성
## Workbench 기본 Python 환경의 RHOAI 패키지와 버전 충돌을 피하기 위해 전용 venv를 사용한다.
rm -rf /opt/app-root/src/.venvs/day06
python3 -m venv /opt/app-root/src/.venvs/day06
source /opt/app-root/src/.venvs/day06/bin/activate
which python

PIP_CONFIG_FILE=./pip.conf python -m pip install -r requirements.txt

python -m pip check
python models/train_iris_sklearn.py
ls iris/

./mc alias set truenas http://192.168.20.5:9000 <MINIO_ID> <MINIO_PW>
./mc mb --ignore-existing truenas/rhoai-models
./mc cp --recursive iris/ truenas/rhoai-models/iris-day6/
./mc ls truenas/rhoai-models/iris-day6/
```

`pip check`는 위 venv를 활성화한 상태에서 실행한다. Workbench 기본 환경에 직접 패키지를 설치하면 Feast 등 이미지에 포함된 다른 도구의 의존성을 변경할 수 있다. 기본 이미지 자체의 `pip check`에는 `appengine-python-standard`와 `urllib3`의 기존 충돌이 표시될 수 있으므로 Day6 venv 검증 결과와 구분한다.

`No matching distribution found`가 다시 발생하면 Nexus 연결뿐 아니라 Workbench와 wheel의 Python ABI가 일치하는지 확인한다.

```bash
python --version
PIP_CONFIG_FILE=./pip.conf python -m pip index versions scikit-learn -vvv
```
> 해당 실습에서는 모델 생성 후 s3 업로드 확인까지만 진행합니다.
> 모델을 .pkl 확장자 파일이 아닌 .joblib 확장자 파일로 생성합니다. 현재 구성된 servingruntim이 MLServer sklearn runtime 이기 때문입니다.
> 단순 .pkl 파일 생성을 실습하고 싶은 경우 .py 파일을 아래 파일로 대체합니다.
```bash
cat > train_iris_sklearn_v2.py<<'EOF'
#!/usr/bin/env python3
import json
import os
import joblib
import pickle	# 추가


OUTDIR = os.path.join(os.getcwd(), "iris")


def main():
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    X, y = load_iris(return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(Xtr, ytr)
    acc = accuracy_score(yte, clf.predict(Xte))
    print(f"accuracy = {acc:.3f}")

    os.makedirs(OUTDIR, exist_ok=True)
    joblib.dump(clf, os.path.join(OUTDIR, "model.joblib"))
    # 아래 2줄 추가
    with open(os.path.join(OUTDIR, "model.pkl"), "wb") as f:
      pickle.dump(clf, f)

    # MLServer v2 inference protocol 요청 예시
    req = {"inputs": [{"name": "input-0", "shape": [1, 4], "datatype": "FP32",
                       "data": Xte[0].tolist()}]}
    json.dump(req, open(os.path.join(OUTDIR, "sample_request.json"), "w"), indent=2)
    print(f"saved -> {OUTDIR}/model.joblib, sample_request.json")


if __name__ == "__main__":
    main()
EOF
```
