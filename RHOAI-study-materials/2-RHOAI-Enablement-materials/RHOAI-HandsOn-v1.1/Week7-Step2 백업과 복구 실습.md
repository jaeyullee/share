# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 7 - Step 2 OADP 백업과 복구

> 사전 준비: [Week7 Step0](<Week7-Step0 사전점검 실습.md>)의 백업 경계와 TrueNAS S3 연결을 확인한다.

OADP 1.6과 File System Backup(FSB, Kopia)을 이용해 Namespace의 Kubernetes 리소스와 NFS PVC 데이터를 S3에 백업하고 삭제 후 복구한다.

### OADP Operator 설치

```bash
oc get packagemanifest redhat-oadp-operator \
  -n openshift-marketplace -o json | jq '{
    source: .status.catalogSource,
    channel: .status.defaultChannel,
    csv: .status.channels[0].currentCSV
  }'
```

OCP 4.22에서는 OADP 1.6을 사용한다. 현재 홈랩 예상값은 `stable`, `oadp-operator.v1.6.0`이다.

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-adp
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: redhat-oadp-operator
  namespace: openshift-adp
spec:
  targetNamespaces:
    - openshift-adp
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: redhat-oadp-operator
  namespace: openshift-adp
spec:
  channel: stable
  installPlanApproval: Automatic
  name: redhat-oadp-operator
  source: cs-redhat-operator-index-v4-22
  sourceNamespace: openshift-marketplace
EOF

oc get subscription,csv,pod -n openshift-adp -w
```

CSV `Succeeded`와 Operator Pod `Running`을 확인하고 감시를 종료한다.

### S3 bucket과 credential 준비

```bash
read -rp 'OADP S3 ID: ' OADP_S3_ID
read -rsp 'OADP S3 PW: ' OADP_S3_PW
echo

mc alias set week7-oadp http://192.168.20.5:9000 \
  "$OADP_S3_ID" "$OADP_S3_PW" --api S3v4
mc mb --ignore-existing week7-oadp/rhoai-week7-oadp

CREDENTIAL_FILE="$(mktemp)"
chmod 600 "$CREDENTIAL_FILE"
cat > "$CREDENTIAL_FILE" <<EOF
[default]
aws_access_key_id=${OADP_S3_ID}
aws_secret_access_key=${OADP_S3_PW}
EOF

oc create secret generic cloud-credentials -n openshift-adp \
  --from-file=cloud="$CREDENTIAL_FILE"

rm -f "$CREDENTIAL_FILE"
unset CREDENTIAL_FILE OADP_S3_ID OADP_S3_PW
```

### DataProtectionApplication 생성

```bash
oc apply -f - <<'EOF'
apiVersion: oadp.openshift.io/v1alpha1
kind: DataProtectionApplication
metadata:
  name: week7-dpa
  namespace: openshift-adp
spec:
  configuration:
    velero:
      defaultPlugins:
        - openshift
        - aws
    nodeAgent:
      enable: true
      uploaderType: kopia
  backupLocations:
    - name: default
      velero:
        provider: aws
        default: true
        credential:
          name: cloud-credentials
          key: cloud
        objectStorage:
          bucket: rhoai-week7-oadp
          prefix: home-lab
        config:
          region: us-east-1
          profile: default
          s3Url: http://192.168.20.5:9000
          s3ForcePathStyle: "true"
          insecureSkipTLSVerify: "true"
EOF

oc get dpa -n openshift-adp
oc get backupstoragelocation -n openshift-adp -w
```

BackupStorageLocation의 `PHASE`가 `Available`이어야 한다. `Unavailable`이면 DPA/Velero 로그, S3 credential, endpoint, bucket을 먼저 확인한다.

```bash
oc get pods -n openshift-adp
oc logs -n openshift-adp deployment/velero -c velero --tail=100
```

### 복구 대상 애플리케이션 생성

```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: week7-dr-lab
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: week7-dr-config
  namespace: week7-dr-lab
data:
  model-stage: Production
  owner: platform-team
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: week7-dr-data
  namespace: week7-dr-lab
spec:
  storageClassName: truenas-nfs
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: week7-dr-writer
  namespace: week7-dr-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: week7-dr-writer
  template:
    metadata:
      labels:
        app: week7-dr-writer
    spec:
      containers:
        - name: writer
          image: registry.redhat.io/ubi9/nginx-126@sha256:10a020f93a6a0c59f0c8d16d3f1cfb7863579dbba847c9ab8bad9fa678a78d1c
          command: [/bin/sh, -c]
          args:
            - |
              printf 'week7-oadp-pvc-data\n' > /data/payload.txt
              sha256sum /data/payload.txt > /data/payload.sha256
              sleep infinity
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 256Mi
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: week7-dr-data
EOF

oc rollout status deployment/week7-dr-writer \
  -n week7-dr-lab --timeout=300s
oc exec -n week7-dr-lab deployment/week7-dr-writer -- \
  sh -c 'cat /data/payload.txt && sha256sum -c /data/payload.sha256'
```

예상 출력은 `week7-oadp-pvc-data`와 `OK`다.

### Backup 생성과 판정

```bash
oc apply -f - <<'EOF'
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: week7-rhoai-app
  namespace: openshift-adp
spec:
  includedNamespaces:
    - week7-dr-lab
  defaultVolumesToFsBackup: true
  ttl: 24h0m0s
EOF

oc wait backup/week7-rhoai-app -n openshift-adp \
  --for=jsonpath='{.status.phase}'=Completed --timeout=900s
oc describe backup week7-rhoai-app -n openshift-adp
mc ls --recursive week7-oadp/rhoai-week7-oadp/home-lab | tail
```

`Phase=Completed`, `Errors=0`, Pod volume backup 완료를 확인한다. `PartiallyFailed`이면 바로 삭제하지 말고 `oc logs deployment/velero`와 `oc get podvolumebackup -n openshift-adp`를 확인한다.

### 삭제 후 Restore

```bash
oc delete namespace week7-dr-lab --wait=true

oc apply -f - <<'EOF'
apiVersion: velero.io/v1
kind: Restore
metadata:
  name: week7-rhoai-app-restore
  namespace: openshift-adp
spec:
  backupName: week7-rhoai-app
  restorePVs: true
EOF

oc wait restore/week7-rhoai-app-restore -n openshift-adp \
  --for=jsonpath='{.status.phase}'=Completed --timeout=900s
oc describe restore week7-rhoai-app-restore -n openshift-adp

oc rollout status deployment/week7-dr-writer \
  -n week7-dr-lab --timeout=300s
oc get configmap week7-dr-config -n week7-dr-lab -o yaml
oc exec -n week7-dr-lab deployment/week7-dr-writer -- \
  sh -c 'cat /data/payload.txt && sha256sum -c /data/payload.sha256'
```

ConfigMap 값과 PVC checksum이 원래 값과 같으면 애플리케이션 복구가 성공한 것이다.

OpenShift Pipelines나 RHOAI가 Namespace 생성 직후 자동으로 다시 만든 RoleBinding과 CA ConfigMap, 이미 존재하는 클러스터 범위 리소스는 Restore `warnings`에 기록될 수 있다. `phase=Completed`인지 확인한 뒤 다음 명령으로 경고 대상을 읽고, 실습 대상 ConfigMap·Deployment·PVC와 checksum이 모두 복구됐으면 성공으로 판정한다. 경고 수만 보고 실패로 판단하지 않는다.

```bash
oc get restore week7-rhoai-app-restore -n openshift-adp \
  -o json | jq '{phase: .status.phase, warnings: .status.warnings, errors: .status.errors}'
oc logs -n openshift-adp deployment/velero -c velero \
  --since=10m | grep -i warning | tail -30
```

### RHOAI 구성 백업의 별도 경계

OADP 전체 클러스터 백업 대신 운영 구성은 GitOps와 정적 export로도 보존한다.

```bash
mkdir -p /tmp/week7-rhoai-config-export
oc get dsci default-dsci -o yaml \
  > /tmp/week7-rhoai-config-export/dsci.yaml
oc get dsc default-dsc -o yaml \
  > /tmp/week7-rhoai-config-export/dsc.yaml
oc get odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications -o yaml \
  > /tmp/week7-rhoai-config-export/dashboard-config.yaml

grep -R -nE 'password|token|access.?key|secret.?key' \
  /tmp/week7-rhoai-config-export || true
```

Secret, Pipeline DB, Model Registry DB, S3 model artifact는 각각 일관성 있는 별도 백업 정책이 필요하다. OADP는 `etcd` backup이나 Operator 재설치 계획을 대체하지 않는다.

### 원복

```bash
oc delete namespace week7-dr-lab --wait=true --ignore-not-found
oc delete restore week7-rhoai-app-restore \
  -n openshift-adp --ignore-not-found

oc apply -f - <<'EOF'
apiVersion: velero.io/v1
kind: DeleteBackupRequest
metadata:
  name: week7-rhoai-app-delete
  namespace: openshift-adp
spec:
  backupName: week7-rhoai-app
EOF

oc wait --for=delete backup/week7-rhoai-app \
  -n openshift-adp --timeout=300s
oc delete dpa week7-dpa -n openshift-adp --ignore-not-found
oc delete secret cloud-credentials -n openshift-adp --ignore-not-found

mc rm --recursive --force week7-oadp/rhoai-week7-oadp || true
mc rb week7-oadp/rhoai-week7-oadp || true
mc alias remove week7-oadp
rm -rf /tmp/week7-rhoai-config-export
```

OADP Operator 설치까지 다시 실습하려면 마지막에 제거한다.

```bash
OADP_CSV="$(oc get subscription redhat-oadp-operator \
  -n openshift-adp -o jsonpath='{.status.installedCSV}')"
OADP_CRDS="$(oc get csv "$OADP_CSV" -n openshift-adp \
  -o json | jq -r '.spec.customresourcedefinitions.owned[].name')"
oc delete subscription redhat-oadp-operator \
  -n openshift-adp --ignore-not-found
test -z "$OADP_CSV" || oc delete csv "$OADP_CSV" \
  -n openshift-adp --ignore-not-found
oc delete namespace openshift-adp --wait=true
printf '%s\n' "$OADP_CRDS" | xargs -r oc delete crd
unset OADP_CSV OADP_CRDS
```

CRD 삭제는 이 실습 외에 OADP/Velero CR을 사용하는 Namespace가 없을 때만 수행한다. 공유 운영 클러스터에서는 Operator 제거와 CRD·백업 데이터 보존을 별도 변경 절차로 다룬다.

### 공식 문서

- [OpenShift 4.22 - OADP application backup and restore](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/backup_and_restore/oadp-application-backup-and-restore)
- [OpenShift 4.22 - Backing up etcd](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/backup_and_restore/control-plane-backup-and-restore)
