# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 7 - 운영관리 보강 사전점검

> 사전 활성화: [Week1 Day1&2](<Week1-Day1&2-환경구성.md>)의 RHOAI 기본 구성, [Week3 Day12](<Week3-Day12 실습.md>)의 Red Hat build of Kueue, [Week3 Day13](<Week3-Day13 실습.md>)의 User Workload Monitoring을 먼저 확인한다.

Week7은 인증, 백업, 분산 워크로드, 관측성과 감사, Kueue 운영, 플랫폼 커스터마이징, 용량 관리를 운영자 관점에서 연결한다. 운영 설정을 변경하므로 시작 상태를 파일로 보존하고 각 Step의 원복 절차를 반드시 수행한다.

### 실습 범위와 경계

| Step | 실습 범위 | 현재 홈랩 기준 |
|---|---|---|
| 1 | RHBK 설치, realm/client/group/user, OpenShift OAuth OIDC, RHOAI 권한 | RHBK Operator 추가 미러 필요 |
| 2 | OADP 1.6, TrueNAS S3, Namespace/PVC 백업·복구 | OADP 패키지는 현재 카탈로그에 있음 |
| 3 | RHOAI KubeRay와 외부 Kueue로 RayJob 실행 | DSC `ray: Removed`를 일시적으로 `Managed`로 전환 |
| 4 | Kueue/RHOAI 메트릭, PrometheusRule, API audit log | User Workload Monitoring 활성화 상태 사용 |
| 5 | Kueue 적체 재현, 원인 판정, quota 변경 후 재입장 | DSC `kueue: Unmanaged`, 외부 Kueue 유지 |
| 6 | Dashboard 앱 타일, 프로젝트 HardwareProfile, 컴포넌트 resource | 변경 전 JSON을 이용해 정확히 원복 |
| 7 | ResourceQuota/LimitRange와 worker 확장 판단 | platform `None`이므로 MachineSet이 아닌 Agent ISO 경로 학습 |

OADP는 애플리케이션 리소스와 PVC를 보호하지만 전체 클러스터, `etcd`, Operator 자체의 DR을 대신하지 않는다. RHBK의 실습용 단일 PostgreSQL과 self-signed 인증서는 기능 검증용이며 운영 구성은 외부 관리형 DB, 조직 CA, HA RHBK를 사용한다.

### 시작 상태 백업

```bash
WEEK7_BACKUP_DIR="/tmp/week7-before-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$WEEK7_BACKUP_DIR"
chmod 700 "$WEEK7_BACKUP_DIR"

oc get oauth cluster -o json > "$WEEK7_BACKUP_DIR/oauth.json"
oc get dsc default-dsc -o json > "$WEEK7_BACKUP_DIR/dsc.json"
oc get odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications -o json \
  > "$WEEK7_BACKUP_DIR/odh-dashboard-config.json"
oc get deployment rhods-dashboard \
  -n redhat-ods-applications -o json \
  > "$WEEK7_BACKUP_DIR/rhods-dashboard.json"

printf 'WEEK7_BACKUP_DIR=%s\n' "$WEEK7_BACKUP_DIR"
```

이 경로는 Step 6까지 유지한다. 파일에는 Secret 값이 없지만 클러스터 구성이 포함되므로 공개 저장소에 커밋하지 않는다.

### Operator와 API 확인

```bash
oc get packagemanifest rhbk-operator redhat-oadp-operator \
  -n openshift-marketplace \
  -o custom-columns='NAME:.metadata.name,CHANNEL:.status.defaultChannel,CSV:.status.channels[0].currentCSV'

oc get csv -A | grep -Ei 'rhods|kueue|cert-manager|oadp|rhbk'
oc get kueues.kueue.openshift.io cluster

oc get dsc default-dsc -o json | jq '.spec.components | {
  ray: .ray.managementState,
  kueue: .kueue.managementState,
  dashboard: .dashboard.managementState
}'

oc get configmap cluster-monitoring-config \
  -n openshift-monitoring \
  -o jsonpath='{.data.config\.yaml}'
```

현재 홈랩의 예상값은 다음과 같다.

- `redhat-oadp-operator`: `stable`, `oadp-operator.v1.6.0`
- `rhbk-operator`: 추가 미러 전에는 `NotFound`, 추가 후 `stable-v26.6`
- DSC: `ray=Removed`, `kueue=Unmanaged`, `dashboard=Managed`
- Kueue CR `cluster`: `Managed`
- monitoring config: `enableUserWorkload: true`

### 인프라와 저장소 확인

```bash
oc get infrastructure cluster -o json | jq '{
  platform: .status.platform,
  controlPlaneTopology: .status.controlPlaneTopology,
  infrastructureTopology: .status.infrastructureTopology
}'

oc get nodes -o wide
oc get storageclass
oc get machineset -n openshift-machine-api

curl -fsS http://192.168.20.5:9000/minio/health/live
```

현재 홈랩은 `platform=None`, control plane/infrastructure `SingleReplica`, StorageClass `truenas-nfs`, MachineSet 없음이 정상이다. 이 조건에서는 MachineSet scale-out 명령을 적용하지 않는다.

### RHBK 카탈로그 판정

폐쇄망 CatalogSource에서 `rhbk-operator`가 조회되지 않으면 Step 1을 시작하지 않는다. 이 자료의 검증 기준은 `stable-v26.6`과 `rhbk-operator.v26.6.4-opr.1`이다. 미러 운영 절차와 registry 인증정보는 공개 실습 범위에 포함하지 않는다.

### 실습 파일 정책

외부 `week7-*.yaml` 파일은 사용하지 않는다. 필요한 선언은 각 Step의 heredoc에 포함되어 있으며 추가 dataset이나 모델 파일도 필요하지 않다.

### 공식 문서

- [RHOAI 3.4 - Managing OpenShift AI](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/managing_openshift_ai/managing_openshift_ai)
- [OpenShift 4.22 - Authentication and authorization](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/authentication_and_authorization/index)
- [OpenShift 4.22 - OADP application backup and restore](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/backup_and_restore/oadp-application-backup-and-restore)
- [Red Hat build of Keycloak 26.6 - Operator Guide](https://docs.redhat.com/en/documentation/red_hat_build_of_keycloak/26.6/html-single/operator_guide/index)
