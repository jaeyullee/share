# MLflow

> ML 라이프사이클 플랫폼 — 실험 추적 + (MLflow 자체) 모델 레지스트리. 3.4에서 GA + DSC managed 승격.
> 영역: [40-파이프라인실험-관계](40-파이프라인실험-관계.md)

---

## 1. 정의 / 역할
- **실험 추적**(log_param/metric/artifact/model) + **MLflow 자체 모델 레지스트리**(버저닝·계보·stage 전환).
- ⚠️ 이 레지스트리는 RHOAI의 별도 **"Model Registry" 컴포넌트와 다른 별개 저장소**(혼동 주의). → [51-Model-Registry](51-Model-Registry.md)

## 2. 버전 / 라이프사이클
- 업스트림 `mlflow/mlflow` + 미드스트림 **`opendatahub-io/mlflow-operator`**(릴리스 1.1).
- 서버 **MLflow 3.10.1**, 권장 SDK `mlflow[kubernetes]>=3.11`.
- **3.4 GA**(TP/DP→fully supported). **DSC managed 컴포넌트로 승격** — 필드명 **`spec.components.mlflowoperator`**(주의: `mlflow` 아님). 과거 dashboard feature flag deprecated.

## 3. 아키텍처
- **컨트롤 플레인**: MLflow Operator가 `MLflow` CR watch → Helm 렌더링 → reconcile. 3.4는 **공유(shared) 트래킹 서버** 프로비저닝.
- **데이터 플레인**: 트래킹 서버 Deployment.
- **백킹 스토어**: 백엔드 DB(sqlite/postgresql, 프로덕션 PostgreSQL 권장) + 아티팩트(file:// PVC / s3:// MinIO).

## 4. CRD: MLflow

| 항목 | 값 |
|---|---|
| group/version | `mlflow.opendatahub.io/v1` |
| kind | `MLflow` (+ 보조 `MLflowConfig`) |
| scope | **소스 불일치**(README namespaced vs RH문서 cluster 싱글톤) — 미확인 |

- 주요 spec: `backendStoreUri(From)`, `registryStoreUri(From)`, `artifactsDestination`, `serveArtifacts`, `storage`(PVC), `replicas`, `image`, `env/envFrom`, `migration`, `garbageCollection`, `caBundleConfigMap`. 인증은 K8s 네이티브(`self_subject_access_review`).

## 5. 배포 리소스
Deployment(트래킹 서버)+Service+ServiceAccount + ConfigMap/Secret(`mlflow-tls`) + PVC + ClusterRole/Binding + NetworkPolicy + DB 마이그레이션 Job + **OpenShift 전용**: ConsoleLink, **Gateway API HTTPRoute**(`/mlflow[-suffix]/api`→`/api` 재작성, 멀티테넌트), ServiceMonitor, service-ca TLS.

## 6. 워크벤치 자동 통합 — `opendatahub.io/mlflow-instance`
노트북 리소스에 어노테이션 → notebook controller가 자동 구성:
- **환경변수 3종 주입**: `MLFLOW_TRACKING_URI=https://<gateway>/mlflow[-<instance>]`, `MLFLOW_K8S_INTEGRATION=true`, `MLFLOW_TRACKING_AUTH=kubernetes-namespaced`.
- **네임스페이스 스코프 RoleBinding 자동 생성**. MLflow SDK 사전설치 이미지와 결합. → [42-Workbenches](42-Workbenches.md)

## 7. 운영 함정
- **두 레지스트리 혼동**: RHOAI Model Registry(거버넌스) ↔ MLflow 레지스트리(실험 계보). 자동 동기화 없음(미확인).
- DSC 필드명 `mlflowoperator`(`mlflow` 아님).
- 서버 3.10.1 vs SDK ≥3.11 정합성.
- GA 신규성으로 소스 간 불일치(scope 등).

## 8. 출처
- 업스트림: https://github.com/mlflow/mlflow
- 오퍼레이터: https://github.com/opendatahub-io/mlflow-operator
- RHOAI 3.4 release notes (MLflow fully supported)

## 9. 미확인/주의
- MLflow CRD scope(`oc get crd mlflows.mlflow.opendatahub.io -o jsonpath='{.spec.scope}'`로 확정).
- DSP↔MLflow 공식 연동, MLflow↔Model Registry 동기화.
