# Feature Store (Feast)

> 오픈소스 Feast 기반 피처 스토어. ML 모델과 데이터 인프라 사이의 다리. training-serving skew·피처 중복·서빙 지연·거버넌스 해결.
> 영역: [50-모델거버넌스-관계](50-모델거버넌스-관계.md)

---

## 1. 정의 / 역할
- 중앙 피처 저장소 + Python SDK/CLI + 다양한 데이터 소스 + RBAC + 데이터 리니지.
- 해결: training-serving skew, 피처 중복, 서빙 지연(sub-ms 온라인 조회), point-in-time correctness.

## 2. 버전 / 라이프사이클
- 업스트림 **`feast-dev/feast`** + 내장 `feast-operator`(Go), RH는 `opendatahub-io/feast` 포크.
- 라이프사이클 = **Technology Preview**(2.20 도입, 3.4까지 TP, 프로덕션 미지원).
- 정확 버전 미확인(v0.59~0.6x 추정).

## 3. 아키텍처 (3대 스토어)
- **Registry(feature registry)**: 피처/엔티티/데이터소스/feature view **메타데이터 카탈로그**. ⚠️ Model Registry와 무관, 이름만 동일.
- **Offline Store**: 학습용 과거 데이터(BigQuery/Redshift/Snowflake/Spark/file/postgres).
- **Online Store**: 추론용 저지연 최신 데이터(Redis/DynamoDB/MySQL/PostgreSQL/Milvus).
- **feast-operator**가 FeatureStore CR을 watch해 서버·서비스·스토리지 배포.

## 4. CRD: FeatureStore

| 항목 | 값 |
|---|---|
| group | `feast.dev` |
| kind / scope | `FeatureStore`(`feast`) / **Namespaced** |
| version | **`v1`** (구 `v1alpha1` deprecated, 신규는 v1) |

- 핵심 spec: `feastProject`(필수), `services`(onlineStore/offlineStore/registry/ui — 각 .server/.persistence{file 또는 store}), `authz`(`kubernetes` RBAC 자동생성 또는 `oidc`), `cronJob`(스케줄 머티리얼라이제이션), `materialization`, `openlineage`(리니지).
- status: `clientConfigMap`(클라이언트 `feature_store.yaml` ConfigMap명), `serviceHostnames`, `phase`.

## 5. CR이 배포하는 것
- **FeatureStore CR당 단일 Deployment**, 활성 서비스를 **한 Pod 내 별도 컨테이너**로 추가(서비스별 별도 Deployment 아님). 클라이언트 `feature_store.yaml` ConfigMap 생성. RHOAI/ODH에선 `odh-trusted-ca-bundle` 마운트.

## 6. 동작 end-to-end
- **Feature View** 정의(데이터 소스 위 시계열 피처 논리 그룹, Python).
- **Materialization**: `feast materialize`가 online store 적재(cronJob 스케줄).
- **조회 2종**: 학습 `get_historical_features()`(point-in-time correct) / 추론 `get_online_features()`(저지연).

## 7. RBAC / 리니지 / Workbench 연동
- RBAC: `authz.kubernetes.roles`로 K8s RBAC 자동생성 또는 `authz.oidc`.
- 리니지: 3.4 신규 **Feature Store Web UI**(등록 객체와 관계 시각화).
- **Workbench 연동(3.4 신규)**: 워크벤치 프로비저닝 시 Feature Store 선택하면 **`feature_store.yaml` 자동 마운트** → Feast SDK로 즉시 접속. → [42-Workbenches](42-Workbenches.md)

## 8. 운영 함정
- TP(프로덕션 미지원·SLA 없음).
- CRD 버전 혼동(예제 `v1alpha1` vs 정식 `v1`).
- operator 배포 시 RBAC 권한 부족 에러(cluster-admin 권장).
- `odh-trusted-ca-bundle` 미구성 시 TLS 실패 가능.

## 9. 출처
- CRD: `feast-dev/feast .../crd/bases/feast.dev_featurestores.yaml` (v1, Namespaced 직접 검증)
- operator: `.../infra/feast-operator/internal/controller/services/services.go`
- RHOAI 3.4 release notes / working-with-machine-learning-features
