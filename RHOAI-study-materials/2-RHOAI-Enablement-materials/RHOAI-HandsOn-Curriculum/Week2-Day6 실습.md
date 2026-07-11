# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 1 - Day6

### gitea 준비
1. gitea 설치 (helm 이용)
2. gitea 콘솔 접속 및 admin 로그인
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

git add .
git commit -m "initial workbench settings"
GIT_SSL_NO_VERIFY=true git push -u origin main

## 필요 라이브러리를 내부 넥서스에 업로드
rm -rf /tmp/wheelhouse
mkdir -p /tmp/wheelhouse
cd /tmp

python3 -m venv /tmp/pypi-upload-venv
source /tmp/pypi-upload-venv/bin/activate
python3 -m pip install --upgrade pip

python3 -m pip download --only-binary=:all: -r /opt/rhoai-data/git-repo/hands-on/day06/requirements.txt -d /tmp/wheelhouse

python -m pip show twine pkginfo
## 설치 안됐으면 아래 진행
# python3 -m pip install \
#   'twine==5.0.0' \
#   'pkginfo==1.12.1.2'

twine upload \
  --repository-url http://192.168.10.50:8081/repository/pypi-hosted/ \
  -u <NEXUS_ID> -p '<NEXUS_PW>' \
  /tmp/wheelhouse/*
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
    notebooks.opendatahub.io/inject-oauth: "true"
spec:
  template:
    spec:
      serviceAccountName: jukebox-workbench
      containers:
        - name: jukebox-workbench
          image: image-registry.openshift-image-registry.svc:5000/redhat-ods-applications/s2i-generic-data-science-notebook:3.4
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "2"
              memory: 4Gi
          env:
            - name: JUPYTER_IMAGE
              value: s2i-generic-data-science-notebook:3.4
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

### 모델 생성&배포
1. Workbench 접속
```bash
## git clone
cd /opt/app-root/src
git clone https://${GIT_USERNAME}:${GIT_TOKEN}@gitea.apps.sno.ocp422.com/hands-on/day06.git
cd day06

## 내부 nexus 이용해서 모델 생성
PIP_CONFIG_FILE=./pip.conf python3 -m pip install -r requirements.txt

python3 -m pip check
python3 models/train_iris_sklearn.py
ls iris/

mc alias set truenas http://192.168.20.5:9000 <MINIO_ID> <MINIO_PW>
mc mb --ignore-existing truenas/rhoai-models
mc cp --recursive iris/ truenas/rhoai-models/iris-day6/
mc ls truenas/rhoai-models/iris-day6/
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
