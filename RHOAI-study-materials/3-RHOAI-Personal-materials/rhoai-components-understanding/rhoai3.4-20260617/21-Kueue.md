# Kueue (Red Hat build of Kueue)

> 잡 큐잉·리소스 쿼터·갱(gang) 스케줄링을 담당하는 쿠버네티스 **잡 admission 컨트롤러**. 분산 워크로드의 공통 게이트.
> 영역: [20-분산워크로드-관계](20-분산워크로드-관계.md)

---

## 1. 정의 / 역할
- 분산 잡은 GPU 같은 비싼 자원을 한꺼번에 점유 → 무작정 띄우면 파편화·데드락. Kueue가 **"언제·누구에게 자원을 줄지"**를 쿼터·우선순위로 판정한다.
- **상위 게이트** 역할. 실제 파드 배치는 admit 이후 kube-scheduler가 수행.

## 2. 업스트림 / 버전 / 라이프사이클
- 업스트림: **`kubernetes-sigs/kueue`**.
- RHOAI: 임베디드 Kueue가 **2.24 deprecated** → **Red Hat build of Kueue(standalone Operator)**로 전환. OCP 4.18+ 필요, 둘 동시 설치 불가.
- 3.4 정확 버전: **미확인** (Kueue 0.14~0.16대 추정). 라이프사이클 GA.

## 3. 아키텍처
- **컨트롤 플레인**: 단일 controller-manager(상주). webhook + 스케줄러 + jobframework 통합.
- **데이터 플레인 없음**: Kueue는 학습 파드를 만들지 않는다. 잡의 `suspend` 필드만 토글하고, 실제 워커 파드는 각 잡 오퍼레이터(KubeRay/Trainer/JobSet/Job)가 생성.

## 4. CRD (group `kueue.x-k8s.io/v1beta1`, Cohort만 v1alpha1)

| CRD | Scope | 역할 |
|---|---|---|
| **ClusterQueue** | Cluster | 쿼터 풀 정의. 워크로드가 이 쿼터 대비 admit |
| **LocalQueue** | Namespaced | 네임스페이스 진입점, ClusterQueue를 가리킴 |
| **ResourceFlavor** | Cluster | 노드 클래스(하드웨어 타입/가격 티어) 정의 |
| **Workload** | Namespaced | 잡마다 Kueue가 만드는 내부 객체(요구+admission 상태) |
| **AdmissionCheck** | Cluster | 쿼터 외 추가 통과 게이트(외부 컨트롤러 처리) |
| **WorkloadPriorityClass** | Cluster | 파드 우선순위와 분리된 Kueue 전용 우선순위 |
| **Cohort** (v1alpha1) | Cluster | ClusterQueue들을 묶어 쿼터 차용(계층형) |

### ClusterQueue 핵심 spec
- `resourceGroups[].flavors[]` — 각 flavor가 ResourceFlavor를 참조 + 자원별 쿼터:
  - **`nominalQuota`** (필수) — **admit 판정의 기준이 되는 장부상 쿼터**.
  - `borrowingLimit` / `lendingLimit` — cohort 차용/대여 상한.
- `cohort` — 차용 그룹(비면 차용 불가).
- `queueingStrategy` — `BestEffortFIFO`(기본) | `StrictFIFO`.
- `preemption` — reclaimWithinCohort / borrowWithinCohort / withinClusterQueue.
- status: `pendingWorkloads` / `admittedWorkloads` / `flavorsUsage`.

### 기타
- **LocalQueue**: `spec.clusterQueue`(불변).
- **ResourceFlavor**: `nodeLabels`(admit 시 파드에 주입), `nodeTaints`, `tolerations`, `topologyName`.
- **Workload**: `podSets[]`(동질 파드 그룹 template+count), `queueName`(=잡의 `queue-name` 라벨). status 조건 **`QuotaReserved`** → **`Admitted`**, 그 외 Finished/Evicted/Preempted.

## 5. CRD 관계 ERD
```
ResourceFlavor (Cluster)
   ▲ 참조: ClusterQueue.resourceGroups[].flavors[].name
ClusterQueue (Cluster) ──spec.cohort──► Cohort (차용·대여)
   ▲ 참조: LocalQueue.spec.clusterQueue
LocalQueue (Namespaced)              ──admissionChecks──► AdmissionCheck (Cluster)
   ▲ 참조: Workload.spec.queueName (= 잡의 kueue.x-k8s.io/queue-name 라벨)
Workload (Namespaced) ── 1:1 ── 하위 Job/JobSet/RayCluster/TrainJob
```

## 6. 동작 방식 (admission end-to-end) ★

1. **Workload 생성(jobframework)**: 지원 잡(Job/JobSet/RayCluster/RayJob/TrainJob 등)을 watch하다 잡마다 podSets·리소스 요구를 미러링한 **Workload 자동 생성**.
2. **트리거 라벨**: 잡에 **`kueue.x-k8s.io/queue-name: <LocalQueue>`**를 달면 opt-in. (우선순위는 `kueue.x-k8s.io/priority-class`)
3. **Suspend로 보류**: webhook이 잡을 `suspend: true`로 잡아둠. 사용자는 평소대로 잡을 만들고, Kueue가 "언제 시작할지" 결정.
4. **쿼터 예약 → admit**: 스케줄러가 대기 Workload에 맞는 flavor를 찾으면 `QuotaReserved`. AdmissionCheck까지 통과 시 **`Admitted`** → 하위 잡의 **`suspend`를 false로** 해제(+ flavor의 nodeSelector/tolerations 주입).
5. **★ 노드 상태가 아닌 nominalQuota 기반**: Kueue는 라이브 노드 용량·kube-scheduler 뷰를 조회하지 않는다. **오직 ClusterQueue의 `nominalQuota`(+cohort borrowing) 대비 현재 예약/사용 쿼터**로만 결정. 실제 배치 가능 여부는 admit 후 kube-scheduler 책임.
6. **★ 갱 스케줄링(all-or-nothing)**: 한 Workload의 모든 podSets는 **하나의 단위로 함께 admit**. 부분 admission 없음. → RayCluster(head+workers), TrainJob(다중 노드)이 원자적으로 admit됨.

## 7. jobframework 통합 (큐잉 가능 타입)
`batch/job`, `ray.io/rayjob`, `ray.io/raycluster`, `jobset.x-k8s.io/jobset`, `kubeflow.org/{pytorchjob,tfjob,mpijob,xgboostjob,paddlejob,jaxjob}`, `pod`, `deployment`, `statefulset`, `leaderworkerset`, `appwrapper` 등. → 활성화 + `queue-name` 라벨이면 자동 Workload 생성·suspend·admit.
- TrainJob 통합: Kueue 0.12엔 없었으나 업스트림이 TrainJob 지원 문서화(최소 Trainer v2.0.0) → 0.14+ 추가 추정. RHOAI 3.4 번들 포함 여부 **미확인**(가능성 높음).

## 8. 운영 함정
- **nominalQuota 과다 설정** → admit 후 Pending(쿼터 통과, 실제 자원 부족). nominalQuota는 시스템 오버헤드 제외 실가용량 반영.
- **부분 스케줄링 데드락**: admit은 갱이나 kube-scheduler 배치는 갱 미보장 → scheduler-plugins Coscheduling 권장. → `../../../5-RHOAI-Delivery-Insights/01-발생-가능한-이슈`
- ResourceFlavor 이름 불일치 시 ClusterQueue `Active=False`(`FlavorNotFound`).
- 임베디드 Kueue와 standalone 동시 설치 불가.

## 9. 출처
- API 소스: https://github.com/kubernetes-sigs/kueue/tree/release-0.12/apis
- 개념/실행: https://kueue.sigs.k8s.io/docs/concepts/workload/ , .../tasks/run/rayclusters/ , .../tasks/run/trainjobs/
- Red Hat Developer: https://developers.redhat.com/articles/2025/12/03/tame-ray-workloads-openshift-ai-kuberay-and-kueue

## 10. 미확인/주의
- 3.4 정확 Kueue 버전(`oc get csv -n openshift-kueue-operator`로 확인).
- TrainJob jobframework 통합 포함 여부.
