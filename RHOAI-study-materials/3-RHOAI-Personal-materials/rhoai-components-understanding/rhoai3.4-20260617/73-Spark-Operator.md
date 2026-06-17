# Kubeflow Spark Operator

> Apache Spark 애플리케이션을 K8s 네이티브 CRD로 제출·관리하는 오퍼레이터. RHOAI의 분산 데이터 처리. 3.4 Developer Preview.
> 영역: [70-가속기데이터UI-관계](70-가속기데이터UI-관계.md)

---

## 1. 정의 / 역할
- 사용자가 `spark-submit`을 직접 다루지 않고 `SparkApplication` CR을 선언하면 라이프사이클(제출/모니터링/재시작) 자동 관리.
- distributed workloads 생태계의 분산 데이터 처리 담당. 활성화: DSC `kubeflowsparkoperator: Managed`.

## 2. 버전 / 라이프사이클
- **RHOAI 3.4 = Developer Preview(DP)** — 프로덕션 미지원, SLA 없음, API 변경 가능.
- 업스트림 `kubeflow/spark-operator`(RH 포크 `red-hat-data-services/spark-operator` rhoai-3.4). **버전 메타 불일치**(VERSION=2.3.0, Chart appVersion=2.4.0), 번들 Apache Spark = **4.0.1**.

## 3. CRD

| 항목 | 값 |
|---|---|
| group/version | `sparkoperator.k8s.io/v1beta2` |
| kinds | `SparkApplication`, `ScheduledSparkApplication` (+`SparkConnect` 언급, 미확인) |
| scope | Namespaced (업스트림 기준, RHOAI 명시 미확인) |

### SparkApplication 핵심 spec
- `type`, `sparkVersion`, `mode`, `image`, `mainClass`, `mainApplicationFile`, `arguments`, `sparkConf`, `deps`(jars/files/pyFiles/packages), `driver`(DriverSpec), `executor`(ExecutorSpec), `dynamicAllocation`(initial/min/maxExecutors), `restartPolicy`(Never/OnFailure/Always).
- driver/executor 공통 `SparkPodSpec`: cores, memory, instances(executor), serviceAccount.

### ScheduledSparkApplication
- `schedule`(cron), `suspend`, `concurrencyPolicy`, `template`.

## 4. 동작 (end-to-end)
오퍼레이터 4구성: (1)SparkApplication Controller → (2)Submission Runner(`spark-submit` 대행) → **driver Pod** → driver가 **executor Pod들** 생성 → (3)Spark Pod Monitor → (4)Mutating Webhook(ConfigMap/volume/affinity 주입).
상태: `SUBMITTED → RUNNING → COMPLETED/FAILED` (+PENDING_RERUN, SUSPENDED 등).

## 5. 연동
- distributed workloads 생태계가 release notes의 유일한 공식 통합 지점.
- **Dashboard/Pipelines/Workbenches 직접 통합 언급 없음** → DP 단계에선 CR(CLI/YAML) 기반 사용(추정).

## 6. 운영 함정
- DP(프로덕션 부적합). 수동 활성화 필요.
- VERSION↔Chart 버전 불일치. v1beta1→v1beta2 마이그레이션.
- mutating webhook 의존. driver가 executor 생성 → serviceAccount/RBAC 필요.
- Dashboard/Pipelines UI 부재.

## 7. 출처
- 소스: `red-hat-data-services/spark-operator` rhoai-3.4
- 업스트림: https://www.kubeflow.org/docs/components/spark-operator/ , https://kubeflow.github.io/spark-operator/docs/api-docs.html
- RHOAI 3.4 release notes (Developer Preview)
