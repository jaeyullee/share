# KubeRay / Ray

> OpenShift에서 Ray 클러스터를 선언형으로 관리·보호하는 오퍼레이터. RHOAI의 분산 컴퓨트(학습/튜닝/배치) 백엔드.
> 영역: [20-분산워크로드-관계](20-분산워크로드-관계.md)

---

## 1. 정의 / 역할
- **Ray** = Python 분산 컴퓨팅 프레임워크. **KubeRay** = 이를 K8s 위에서 돌리는 오퍼레이터.
- RHOAI에서 유연한 Python 기반 분산 워크로드(학습·하이퍼파라미터 튜닝·데이터 처리·배치)의 실행 엔진.

## 2. 왜 cluster인가
분산은 한 Pod에 안 담긴다. 여러 노드의 GPU를 쓰려면 본질적으로 여러 Pod이 필요하고, 그것들이 한 작업을 같이 하려면 서로 찾고 통신해야 한다 → 그 협력 구조가 **cluster**. "여러 머신을 한 대처럼" 쓰게 해주는 런타임이 Ray cluster.

## 3. 버전 / 라이프사이클
- 업스트림: **`ray-project/kuberay`** (KubeRay **1.4.2**) + `ray-project/ray` (런타임 **2.53.0**, Py3.12, CUDA 12.8/ROCm 6.4).
- 라이프사이클: GA. (참고: **CodeFlare Operator는 3.0에서 removed** — 기능은 KubeRay + Kueue + cert-manager + NetworkPolicy로 이관.)

## 4. 아키텍처 (★컨트롤 vs 데이터 + 2층 스케줄링)
- **컨트롤 플레인(상주)**: 단일 controller-manager. RayCluster/RayJob/RayService 리컨실러 3개 등록.
- **데이터 플레인(잡별)**: RayCluster마다 **head 파드 1개 + worker 파드 N개**.
  - head: GCS(Global Control Store, 클러스터 메타·상태) + Ray 스케줄러 + 대시보드 + (autoscaling 시) autoscaler 사이드카.
  - worker: raylet(로컬 스케줄러 + object store 조각) + worker 프로세스(실제 연산).

### 2층 스케줄링 (헷갈림 주의)
```
[1층 K8s] KubeRay가 head+worker Pod 생성 → kube-scheduler 노드 배치  (cluster 세울 때 1회)
[2층 Ray] 학습 task/actor를 Ray 스케줄러가 "이미 뜬 worker 안에" 배치  (새 Pod 안 만듦)
```
→ **학습은 새 파드 배포가 아니라 기존 worker 안에서 task로 돈다.** RayCluster = 학습이 올라타는 무대(파드 묶음) 그 자체. 단 그 파드를 만든 건 KubeRay 오퍼레이터.

## 5. CRD (group `ray.io/v1`, Namespaced)

| CRD | 역할 |
|---|---|
| **RayCluster** | head + worker로 구성된 상주 클러스터 |
| **RayJob** | 잡 제출 시 임시 RayCluster 생성, 끝나면 정리 |
| **RayService** | Ray Serve 기반 서빙(추론) |

### RayCluster 핵심 spec
- `headGroupSpec` (replicas 없음 — head는 항상 1), `rayStartParams`, `template`.
- `workerGroupSpecs[]`: `groupName` / `replicas` / `minReplicas` / `maxReplicas` / `template`.
- `rayVersion`, `enableInTreeAutoscaling`, `autoscalerOptions`.
- **`suspend`**: true면 head·worker 파드 전부 삭제 → 자원 소비 0 (Kueue가 이 필드로 admission 제어).

### RayJob 핵심 spec
- `rayClusterSpec`(템플릿) 또는 `clusterSelector`(기존 재사용), `entrypoint`, `submissionMode`(K8sJobMode 기본), `shutdownAfterJobFinishes`, `ttlSecondsAfterFinished`, **`suspend`**.

## 6. Kueue 연동
- RayCluster/RayJob 라벨에 `kueue.x-k8s.io/queue-name` → suspended로 생성 → Kueue admit 시 `spec.suspend`를 false로 unsuspend. admit 전엔 쿼터 미소비. 선점 시 다시 suspend → 파드 제거.

## 7. 동작 end-to-end
1. (SDK 또는 YAML) RayCluster 생성, queue-name 라벨, suspend.
2. Kueue admit → unsuspend.
3. KubeRay가 head+worker 파드 생성.
4. head GCS 기동 → worker 등록 → cluster ready.
5. 클라이언트가 `ray.init`/RayJobClient로 task 제출 → Ray 스케줄러가 worker에 분산.

## 8. 운영 함정
- Ray 버전과 KubeRay 버전 호환 필요(3.4: KubeRay 1.4.2 + Ray 2.53.0). 임의 Ray 이미지 혼용 주의.
- mTLS는 3.0+ cert-manager 기반. 네트워크 격리는 KubeRay가 NetworkPolicy로.
- worker 일부만 떠서 GPU 물고 늘어지는 부분 스케줄링 데드락(→ [21-Kueue](21-Kueue.md)).

## 9. 출처
- API 소스: https://github.com/ray-project/kuberay/tree/master/ray-operator/apis/ray/v1
- Red Hat Developer: https://developers.redhat.com/articles/2025/12/03/tame-ray-workloads-openshift-ai-kuberay-and-kueue
