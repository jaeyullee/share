# CodeFlare SDK

> 노트북에서 K8s YAML/kubectl 없이 Ray 클러스터·잡을 정의·제출하는 **Python 클라이언트 SDK**. 분산학습의 입구.
> 영역: [20-분산워크로드-관계](20-분산워크로드-관계.md)

---

## 1. 정의 / 역할
- CRD/오퍼레이터가 **아니다**. 노트북에서 쓰는 **클라이언트 측 Python 라이브러리**.
- RayCluster CR 작성 + Kueue 큐 연동을 `cluster.apply()` 한 줄로 추상화. 데이터 사이언티스트가 인프라(YAML/CRD)를 몰라도 분산 자원을 받아 쓰게 해줌.

> 구분: **CodeFlare SDK**(클라이언트 라이브러리) ≠ **CodeFlare Operator**(서버 측, **3.0에서 removed**). SDK는 별개로 존속.

## 2. 버전 / 라이프사이클
- 업스트림: **`project-codeflare/codeflare-sdk`** (0.34). workbench 이미지 동봉. 라이프사이클 GA.
- **3.0+에서 SDK는 KubeRay + Kueue와 직접 통신** (과거 MCAD/AppWrapper 경유 없음). 2.x 문서의 "CodeFlare operator가 MCAD/InstaScale 설치" 서술은 obsolete.

## 3. 생성 객체 + 워크플로
- `Cluster(ClusterConfiguration(...))`가 **RayCluster CR**(`ray.io/v1`) 빌드 + `kueue.x-k8s.io/queue-name` 라벨 부착(`local_queue` 미지정 시 기본 큐 자동 탐색).
- 흐름:
  ```
  노트북 → Cluster(...).apply() → suspended RayCluster 생성
        → Kueue admit → KubeRay가 head+worker 파드 생성
        → .wait_ready()/.status()/.details()
        → 잡 제출(cluster.job_client = RayJobClient → submit_job(entrypoint=...))
        → .down()
  ```

```python
from codeflare_sdk import Cluster, ClusterConfiguration
cluster = Cluster(ClusterConfiguration(
    name="my-ray", namespace="my-project",
    num_workers=4,
    worker_cpu_requests=8, worker_memory_requests="32Gi",
    worker_extended_resource_requests={"nvidia.com/gpu": 1},
    local_queue="my-localqueue",
))
cluster.apply()      # RayCluster 생성 → Kueue 큐 제출
cluster.wait_ready()
# ... Ray 작업 ...
cluster.down()
```

## 4. ClusterConfiguration 주요 파라미터
- `name`(필수), `namespace`, `num_workers`, `image`, `local_queue`.
- head: `head_cpu_requests`/`head_cpu_limits`/`head_memory_requests`/`head_memory_limits`/`head_extended_resource_requests`.
- worker: `worker_cpu_requests`/`worker_cpu_limits`/`worker_memory_requests`/`worker_memory_limits`/`worker_extended_resource_requests`(GPU).
- `enable_autoscaling`/`min_workers`/`max_workers`, `volumes`/`volume_mounts`.

## 5. Deprecated/제거된 파라미터 (★주의)
| Old | New |
|---|---|
| `head_gpus` | `head_extended_resource_requests['nvidia.com/gpu']` |
| `num_gpus` | `worker_extended_resource_requests['nvidia.com/gpu']` |
| `min_cpus`/`max_cpus` | `worker_cpu_requests`/`worker_cpu_limits` |
| `min_memory`/`max_memory` | `worker_memory_requests`/`worker_memory_limits` |
| `head_cpus` / `head_memory`(단일) | requests/limits로 분리 |

- `appwrapper`, `template`, `head_info`, `machine_types`는 현행에서 제거(`appwrapper` 제거 = 3.0 AppWrapper/MCAD 제거와 정합).
- 제출 메서드는 **`.apply()`** (구 `.up()` 아님).

## 6. 다른 컴포넌트와의 연동
- **KubeRay**: RayCluster CR을 만들어 KubeRay가 파드 생성 → [22-KubeRay-Ray](22-KubeRay-Ray.md)
- **Kueue**: `local_queue`로 큐 연동 → admission → [21-Kueue](21-Kueue.md)

## 7. 운영 함정
- 구 파라미터(`head_gpus` 등) 쓰면 동작 안 함 → 신 파라미터로.
- `.apply()` 후 Kueue admit 대기(쿼터 부족 시 안 뜸).

## 8. 출처
- 소스: https://github.com/project-codeflare/codeflare-sdk/blob/main/src/codeflare_sdk/ray/cluster/config.py
