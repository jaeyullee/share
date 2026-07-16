# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 4 - Step 1 GPU 공유 슬롯 구성

> 사전 활성화: [Week4 사전점검](<Week4-Step0 사전점검 실습.md>)을 완료하고 [Week3 Day11](<Week3-Day11 실습.md>)의 GPU가 정상인지 확인한다.

물리 GPU 1개를 Time-Slicing 접근 슬롯 4개로 노출한다. 원본 탭의 Time-Slicing 2개와 MPS 2개 동시 구성은 지원되지 않으므로 수행하지 않는다.

### Time-Slicing 설정 적용
```bash
oc apply -f - <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: week4-gpu-sharing
  namespace: nvidia-gpu-operator
data:
  time-slicing-4: |-
    version: v1
    flags:
      migStrategy: none
    sharing:
      timeSlicing:
        renameByDefault: false
        failRequestsGreaterThanOne: true
        resources:
          - name: nvidia.com/gpu
            replicas: 4
  mps-4: |-
    version: v1
    flags:
      migStrategy: none
    sharing:
      mps:
        renameByDefault: false
        resources:
          - name: nvidia.com/gpu
            replicas: 4
EOF

oc patch clusterpolicy gpu-cluster-policy --type=merge \
  -p '{"spec":{"devicePlugin":{"config":{"name":"week4-gpu-sharing"}}}}'

oc label node ocp-w01-gpu \
  nvidia.com/device-plugin.config=time-slicing-4 --overwrite
```

노드 label 변경 후 config manager가 Device Plugin 설정을 다시 읽는다.

```bash
oc get pods -n nvidia-gpu-operator -w
```

모든 관련 Pod가 다시 `Running`이 되면 `Ctrl+C`로 종료한다.

### 슬롯과 공유 방식 확인
```bash
oc get node ocp-w01-gpu \
  -o jsonpath='{.status.capacity.nvidia\.com/gpu}{"/"}{.status.allocatable.nvidia\.com/gpu}{"\n"}'

oc get node ocp-w01-gpu \
  -o jsonpath='{.metadata.labels.nvidia\.com/gpu\.sharing-strategy}{"\n"}{.metadata.labels.nvidia\.com/gpu\.replicas}{"\n"}'
```

예상값은 다음과 같다.

```text
4/4
time-slicing
4
```

이 숫자는 GPU 메모리 4등분이나 25% 연산 성능 보장을 뜻하지 않는다. 네 Pod는 같은 GPU 메모리와 장애 영역을 공유하고 CUDA 실행 시간을 서로 나눠 쓴다.

### 선택 실습: 노드 전체를 MPS로 전환
Steps 2~6은 Time-Slicing을 기준으로 하므로 다음 비교는 선택 사항이다. 실행 중인 GPU workload를 모두 제거한 뒤에만 전환한다.

```bash
oc label node ocp-w01-gpu \
  nvidia.com/device-plugin.config=mps-4 --overwrite

oc get pods -n nvidia-gpu-operator
oc get node ocp-w01-gpu \
  -o jsonpath='{.metadata.labels.nvidia\.com/gpu\.sharing-strategy}{"\n"}{.status.allocatable.nvidia\.com/gpu}{"\n"}'
```

MPS는 control daemon이 각 replica의 GPU 메모리와 연산 비율을 나누지만 NVIDIA Kubernetes Device Plugin 문서에서는 experimental로 표시된다. RTX 5060 Ti와 현재 GPU Operator 조합에서 MPS 관련 Pod가 준비되지 않으면 이벤트와 daemon 로그만 수집하고 기본 실습 경로로 돌아간다.

```bash
oc get events -n nvidia-gpu-operator --sort-by=.lastTimestamp | tail -30
oc get pods -n nvidia-gpu-operator | grep -i mps

# Steps 2~6을 위한 기본 상태로 복귀
oc label node ocp-w01-gpu \
  nvidia.com/device-plugin.config=time-slicing-4 --overwrite
```

### 확인 기준
- 물리 GPU는 1개지만 `nvidia.com/gpu` capacity/allocatable은 4다.
- `nvidia.com/gpu.sharing-strategy`는 Steps 2~6 시작 전에 `time-slicing`이다.
- `failRequestsGreaterThanOne: true`이므로 각 컨테이너는 공유 GPU를 1개만 요청해야 한다.
