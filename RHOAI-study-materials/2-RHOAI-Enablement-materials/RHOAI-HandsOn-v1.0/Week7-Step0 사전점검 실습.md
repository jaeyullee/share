# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 7 - 운영관리 보강 사전점검

> **환경별 재확인**: platform type, control plane topology, StorageClass, MachineSet, OADP/RHBK/Ray channel과 backup endpoint는 검증 환경 값이다. 각 Step 전에 현재 클러스터 값을 수집해 적용 가능 여부를 판정한다. 공통 경계 조건은 [실습자료 검토 항목](<00-실습자료-검토항목.md#환경별-재확인>)을 참고한다.

> **Technology Preview 경계:** RHCL의 OIDC `AuthPolicy` 기능 자체와 RHCL 제품 전체를 TP로 분류하지 않는다. 이 환경에서 사용하는 RHCL 1.4.1 **disconnected 설치 방식**과 RHOAI 3.4 MaaS **external OIDC 연동**이 각각 TP다. Week7 Step2의 필수 RHCL 정책 실습과 선택 MaaS external OIDC 실습의 지원 범위를 구분한다.

> 사전 활성화: [Week1 Day1&2](<Week1-Day1&2-환경구성.md>)의 RHOAI 기본 구성, [Week3 Day12](<Week3-Day12 실습.md>)의 Red Hat build of Kueue, [Week3 Day13](<Week3-Day13 실습.md>)의 User Workload Monitoring, [Week3 Day14](<Week3-Day14 실습.md>)의 RHCL operand와 MaaS를 먼저 확인한다.

Week7은 인증, 백업, 분산 워크로드, 관측성과 감사, Kueue 운영, 플랫폼 커스터마이징, 용량 관리를 운영자 관점에서 연결한다. 운영 설정을 변경하므로 시작 상태를 파일로 보존하고 각 Step의 원복 절차를 반드시 수행한다.

### 실습 범위와 경계

| Step | 실습 범위 | 검증 환경 기준 |
|---|---|---|
| 1 | RHBK 설치, realm/client/group/user, OpenShift OAuth OIDC, RHOAI 권한 | RHBK Operator 추가 미러 필요 |
| 2 | RHBK JWT, RHCL OIDC `AuthPolicy`, 선택 MaaS external OIDC | RHCL disconnected 설치와 MaaS external OIDC는 각각 TP 경계 명시 |
| 3 | OADP 1.6, TrueNAS S3, Namespace/PVC 백업·복구 | OADP 패키지는 현재 카탈로그에 있음 |
| 4 | RHOAI KubeRay와 외부 Kueue로 RayJob 실행 | DSC `ray: Removed`를 일시적으로 `Managed`로 전환 |
| 5 | Kueue/RHOAI 메트릭, PrometheusRule, API audit log | User Workload Monitoring 활성화 상태 사용 |
| 6 | Kueue 적체 재현, 원인 판정, quota 변경 후 재입장 | DSC `kueue: Unmanaged`, 외부 Kueue 유지 |
| 7 | Dashboard 앱 타일, 프로젝트 HardwareProfile, 컴포넌트 resource | 변경 전 JSON을 이용해 정확히 원복 |
| 8 | ResourceQuota/LimitRange와 worker 확장 판단 | platform `None`이므로 MachineSet이 아닌 Agent ISO 경로 학습 |

OADP는 애플리케이션 리소스와 PVC를 보호하지만 전체 클러스터, `etcd`, Operator 자체의 DR을 대신하지 않는다. RHBK의 실습용 단일 PostgreSQL과 self-signed 인증서는 기능 검증용이며 운영 구성은 외부 관리형 DB, 조직 CA, HA RHBK를 사용한다.

### Step2 선행 구성과 소유권

Week7 Step2는 새 Operator를 설치하지 않는다. 앞선 기본 과정을 순서대로 수행했다는 전제에서 Week3 Day14의 RHCL·Kuadrant·Authorino·Limitador와 MaaS를 재사용하고, Week7 Step1이 만든 RHBK realm과 사용자를 이어서 사용한다.

| 구성 | 준비 단계 | Step2 처리 |
|---|---|---|
| RHCL과 dependency operand | Week3 Day14 | 유지하고 `AuthPolicy` 검증에 사용 |
| MaaS Tenant와 Gateway | Week3 Day14 | 선택 external OIDC TP에서만 설정을 일시 변경 |
| RHBK realm/client/user/group | Week7 Step1 | 유지하고 JWT issuer로 사용 |
| Gateway·HTTPRoute·검증 backend | Week7 Step2 | 전용 Namespace에 생성 후 삭제 |

Week7 Step1 원복을 먼저 실행했다면 Step2로 진행하지 말고 Step1을 다시 수행한다. RHCL 1.4.1 disconnected 설치 절차의 TP 경계는 유지되므로, 다른 환경에서는 설치 시점의 지원 상태와 catalog 구성을 다시 확인한다.

### 시작 상태 백업

```bash
export WEEK7_BACKUP_DIR="/tmp/week7-before-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$WEEK7_BACKUP_DIR"
chmod 700 "$WEEK7_BACKUP_DIR"

oc get oauth cluster -o json > "$WEEK7_BACKUP_DIR/oauth.json"
oc get console.config.openshift.io cluster -o json \
  > "$WEEK7_BACKUP_DIR/console.json"
oc get dsc default-dsc -o json > "$WEEK7_BACKUP_DIR/dsc.json"
oc get odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications -o json \
  > "$WEEK7_BACKUP_DIR/odh-dashboard-config.json"
oc get deployment rhods-dashboard \
  -n redhat-ods-applications -o json \
  > "$WEEK7_BACKUP_DIR/rhods-dashboard.json"
oc get subscription,csv -A -o json \
  > "$WEEK7_BACKUP_DIR/olm.json"
oc get namespace -o json \
  > "$WEEK7_BACKUP_DIR/namespaces.json"
oc get gateway,httproute -A -o json \
  > "$WEEK7_BACKUP_DIR/gateway-api.json"
oc get route -A -o json \
  > "$WEEK7_BACKUP_DIR/routes.json"

if oc api-resources --api-group=kuadrant.io -o name | grep -q '^kuadrants\.'; then
  oc get kuadrant,authpolicy,ratelimitpolicy -A -o json \
    > "$WEEK7_BACKUP_DIR/rhcl.json"
else
  printf '{"apiVersion":"v1","items":[],"kind":"List"}\n' \
    > "$WEEK7_BACKUP_DIR/rhcl.json"
fi

if oc get tenant default-tenant -n models-as-a-service \
  -o json > "$WEEK7_BACKUP_DIR/maas-tenant.json" 2>/dev/null; then
  :
else
  printf '{"present":false}\n' > "$WEEK7_BACKUP_DIR/maas-tenant.json"
fi

printf 'WEEK7_BACKUP_DIR=%s\n' "$WEEK7_BACKUP_DIR"
```

이 경로는 Step 8까지 유지한다. SSH를 다시 접속하면 환경변수는 사라지므로, 각 원복 절의 백업 경로 선택 블록에서 이 디렉터리를 다시 선택해 `export`한다. 파일에는 Secret 값이 없지만 클러스터 구성이 포함되므로 공개 저장소에 커밋하지 않는다.

### Operator와 API 확인

```bash
oc get packagemanifest \
  rhbk-operator redhat-oadp-operator rhcl-operator \
  dns-operator authorino-operator limitador-operator \
  -n openshift-marketplace \
  -o custom-columns='NAME:.metadata.name,CHANNEL:.status.defaultChannel,CSV:.status.channels[0].currentCSV'

oc get csv -A | grep -Ei \
  'rhods|kueue|cert-manager|oadp|rhbk|rhcl|authorino|limitador|dns-operator'
oc get kueues.kueue.openshift.io cluster

oc get dsc default-dsc -o json | jq '.spec.components | {
  ray: .ray.managementState,
  kueue: .kueue.managementState,
  dashboard: .dashboard.managementState,
  modelsAsService: .kserve.modelsAsService.managementState
}'

oc get configmap cluster-monitoring-config \
  -n openshift-monitoring \
  -o jsonpath='{.data.config\.yaml}'
```

검증 환경의 예상값은 다음과 같다.

- `redhat-oadp-operator`: `stable`, `oadp-operator.v1.6.0`
- `rhbk-operator`: 추가 미러 전에는 `NotFound`, 추가 후 `stable-v26.6`
- `rhcl-operator`: `stable`, `rhcl-operator.v1.4.1`
- RHCL dependency: DNS `1.4.0`, Authorino `1.4.1`, Limitador `1.4.0`
- DSC: `ray=Removed`, `kueue=Unmanaged`, `dashboard=Managed`; MaaS는 이전 실습 유지 여부에 따라 `Managed` 또는 `Removed`
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

검증 환경은 `platform=None`, control plane/infrastructure `SingleReplica`, StorageClass `truenas-nfs`, MachineSet 없음이 정상이다. 이 조건에서는 MachineSet scale-out 명령을 적용하지 않는다.

### RHBK 카탈로그 판정

폐쇄망 CatalogSource에서 `rhbk-operator`가 조회되지 않으면 Step 1을 시작하지 않는다. 이 자료의 검증 기준은 `stable-v26.6`과 `rhbk-operator.v26.6.4-opr.1`이다. 미러 운영 절차와 registry 인증정보는 공개 실습 범위에 포함하지 않는다.

### 실습 파일 정책

외부 `week7-*.yaml` 파일은 사용하지 않는다. 필요한 선언은 각 Step의 heredoc에 포함되어 있으며 추가 dataset이나 모델 파일도 필요하지 않다.

### 공식 문서

- [RHOAI 3.4 - Managing OpenShift AI](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/managing_openshift_ai/managing_openshift_ai)
- [OpenShift 4.22 - Authentication and authorization](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html-single/authentication_and_authorization/index)
- [OpenShift 4.22 - OADP application backup and restore](https://docs.redhat.com/en/documentation/openshift_container_platform/4.22/html/backup_and_restore/oadp-application-backup-and-restore)
- [Red Hat build of Keycloak 26.6 - Operator Guide](https://docs.redhat.com/en/documentation/red_hat_build_of_keycloak/26.6/html-single/operator_guide/index)
- [RHCL 1.4 - Installing in a disconnected environment](https://docs.redhat.com/en/documentation/red_hat_connectivity_link/1.4/html/installing_connectivity_link/rhcl-install-disconnected)
- [RHOAI 3.4 - Configure external OIDC authentication for MaaS](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html/govern_llm_access_with_models-as-a-service/deploy-and-manage-models-as-a-service_maas#configure-external-oidc-authentication-for-models-as-a-service_deploy-and-manage-models-as-a-service)
