# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 6 - Step 4 TP1/TP2 비교와 원복

> 사전 활성화: [Week6 Step 3](<Week6-Step3 TP2 실습.md>)의 두 rank, 두 GPU process와 API 요청 성공을 확인한다.

TP1과 TP2의 기능·자원·지연 차이를 정리하고 실습 리소스와 선택적으로 제거한 Dashboard를 원복한다.

### 측정 결과 요약

```bash
printf '%-6s %-18s %-18s\n' MODE AVG_TTFB AVG_TOTAL
for MODE in tp1 tp2; do
  awk -v mode="$MODE" '
    NR > 2 {ttfb += $2; total += $3; count++}
    END {printf "%-6s %-18.6f %-18.6f\n", mode, ttfb/count, total/count}
  ' "/tmp/week6-${MODE}-times.tsv"
done

cat /tmp/week6-tp1-startup.json
cat /tmp/week6-tp2-startup.json
```

`NR > 2`는 header와 cold first request를 제외하고 warm 요청 2~5 평균을 계산한다. 시작 시간은 `created`와 Ready condition의 `lastTransitionTime` 차이로 비교한다.

다음 표에 관찰값을 기록한다.

| 항목 | TP1 | TP2 | 해석 |
|---|---:|---:|---|
| predictor GPU request | 1 | 2 | TP2는 물리 GPU 두 장을 한 Pod에 할당 |
| vLLM world size | 1 | 2 | 두 rank 생성 여부 |
| 모델 Ready까지 시간 | 기록 | 기록 | TP2 process/NCCL 초기화 비용 포함 |
| warm 평균 TTFB | 기록 | 기록 | 첫 token 응답 지연 |
| warm 평균 total | 기록 | 기록 | 64 token 제한 요청 총시간 |
| GPU별 memory.used | 기록 | 기록 | TP2 양쪽 GPU 사용 여부 |
| NCCL transport | 없음 | 기록 | PCIe/SHM/P2P 경로 |

### 결과 해석

이번 결과에서 TP2가 TP1보다 느려도 기능 검증은 성공할 수 있다.

- 모델이 0.5B라 한 GPU에서 memory pressure가 없다.
- Tensor Parallel은 각 layer에서 rank 간 collective 통신이 발생한다.
- RTX 5060 Ti 두 장 사이에는 NVLink가 없어 PCIe/host 경로 비용이 크다.
- TP는 주로 한 GPU memory에 들어가지 않는 모델을 분할하거나, 충분히 큰 연산에서 통신비보다 병렬화 이득이 클 때 사용한다.

vLLM 공식 문서도 NVLink가 없는 GPU에서는 모델 구조와 환경에 따라 Pipeline Parallel이 통신 오버헤드 측면에서 더 나을 수 있다고 설명한다. 이 Week6의 합격 기준은 속도 향상이 아니라 **두 물리 GPU에서 TP2 rank가 동작하고 같은 API 요청을 처리하는 것**이다.

### TP 리소스 삭제

```bash
oc delete isvc week6-qwen-tp2 -n rhoai-tp-lab --ignore-not-found
oc wait --for=delete deployment/week6-qwen-tp2-predictor \
  -n rhoai-tp-lab --timeout=300s || true
oc delete servingruntime week6-vllm-tp2 \
  -n rhoai-tp-lab --ignore-not-found

oc delete namespace rhoai-tp-lab --ignore-not-found
oc wait --for=delete namespace/rhoai-tp-lab --timeout=300s
```

Namespace 삭제로 ModelCar pull Secret과 남아 있는 Job, Pod, Service가 함께 제거된다.

### Dashboard 원복

Step 1의 선택 절차를 수행한 경우에만 백업값을 복원한다. 백업 파일이 없으면 이 블록을 실행하지 않는다.

```bash
if [ -s /tmp/week6-dashboard-before.json ]; then
  DASHBOARD_BEFORE=$(cat /tmp/week6-dashboard-before.json)
  oc patch dsc default-dsc --type=merge \
    -p "{\"spec\":{\"components\":{\"dashboard\":$DASHBOARD_BEFORE}}}"
  oc wait --for=condition=Ready dsc/default-dsc --timeout=600s
fi

oc get dsc default-dsc -o json | \
  jq '.spec.components.dashboard'
```

원래 값이 `Managed`였다면 Dashboard Pod가 다시 Ready가 되는지 확인한다.

```bash
oc get pods -n redhat-ods-applications | grep rhods-dashboard || true
```

### 임시 파일 정리

```bash
rm -f /tmp/week6-dashboard-before.json \
  /tmp/week6-chat-request.json \
  /tmp/week6-tp1-startup.json /tmp/week6-tp2-startup.json \
  /tmp/week6-tp1-times.tsv /tmp/week6-tp2-times.tsv \
  /tmp/week6-tp1-response-*.json /tmp/week6-tp2-response-*.json \
  /tmp/week6-tp1-port-forward.log /tmp/week6-tp2-port-forward.log \
  /tmp/week6-tp2-parallel.log
```

각 Step에서 PID를 종료했기 때문에 18092/18093 port-forward가 남아 있으면 안 된다.

```bash
ss -lntp | grep -E ':18092|:18093' || true
```

### 두 번째 GPU passthrough의 처리

두 번째 GPU는 이후 실습과 운영 검토에 재사용할 수 있으므로 기본 정리에서는 VM 102에 유지한다. Proxmox host로 돌려야 할 때만 maintenance window에 다음을 실행한다.

```bash
qm shutdown 102 --timeout 120
qm set 102 --delete hostpci1
qm start 102
```

제거했다면 worker Ready 복귀 후 GPU capacity가 다시 `1/1`인지 확인한다. 유지했다면 `2/2`가 정상이다.

### 최종 확인

```bash
oc get namespace rhoai-tp-lab
oc get isvc,servingruntime -A | grep week6 || true
oc get dsc default-dsc
oc get clusterpolicy gpu-cluster-policy
oc get node ocp-w01-gpu \
  -o jsonpath='{.status.capacity.nvidia\.com/gpu}{"/"}{.status.allocatable.nvidia\.com/gpu}{"\n"}'
```

- Week6 Namespace와 serving 리소스가 없다.
- DSC와 ClusterPolicy가 Ready다.
- Dashboard를 임시 제거했다면 원래 management state로 돌아왔다.
- Device Plugin 공유 설정은 변경하지 않았다.
- 두 번째 passthrough를 유지하면 GPU capacity/allocatable은 `2/2`다.
