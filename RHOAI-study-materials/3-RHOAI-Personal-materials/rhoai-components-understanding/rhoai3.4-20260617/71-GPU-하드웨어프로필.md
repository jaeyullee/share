# GPU / 하드웨어 프로필 (HardwareProfile)

> 워크로드가 요청할 리소스(CPU/Memory/Accelerator) + 배치·스케줄링 정책을 한 객체로 묶은 RHOAI 추상화. 3.4 GA, AcceleratorProfile 대체.
> 영역: [70-가속기데이터UI-관계](70-가속기데이터UI-관계.md)

---

## 1. 정의 / 역할
- 사용자는 dashboard에서 워크벤치/서빙/파이프라인 생성 시 프로파일을 고르기만 하고, RHOAI가 이를 pod의 resource requests/limits + nodeSelector/tolerations 또는 Kueue 큐 제출로 변환.
- **3.4 GA**. AcceleratorProfile + 워크벤치 Container Size selector 통합 대체.

## 2. 버전 / 라이프사이클
- 업스트림 `opendatahub-io/opendatahub-operator` (`api/infrastructure/v1/hardwareprofile_types.go`).
- API `infrastructure.opendatahub.io/v1`(storage), `v1alpha1` deprecated. **3.4 GA**.
- AcceleratorProfile: 3.0 deprecated, 완전 removal 시점 미확인(dashboard 코드에 modelmesh/fine-tuning용 잔존).

## 3. CRD 스키마 (소스 확인)

| 항목 | 값 |
|---|---|
| group/version/kind | `infrastructure.opendatahub.io/v1`, `HardwareProfile` |
| scope | Namespaced (RHOAI `redhat-ods-applications`, 프로젝트 스코프도) |

```
HardwareProfileSpec:
  identifiers []HardwareIdentifier   # CPU/Memory/Accelerator 배열
  scheduling  *SchedulingSpec

HardwareIdentifier:
  displayName / identifier (예 nvidia.com/gpu) / minCount / maxCount / defaultCount
  resourceType: CPU | Memory | Accelerator

SchedulingSpec (상호배타, CEL 검증):
  type: "Queue" | "Node"
  kueue: { localQueueName(필수); priorityClass }   # type=Queue
  node:  { nodeSelector; tolerations }              # type=Node
```

> ★ `nodeSelector`/`tolerations`는 최상위가 아니라 **`spec.scheduling.node` 하위**. `scheduling.type`이 Queue/Node 택1로 CEL admission 강제. 표시 메타(display-name/disabled)는 `metadata.annotations`.

## 4. 워크로드 소비 (end-to-end)
1. dashboard에서 프로파일 선택 + 수량(min~max).
2. 각 identifier(`nvidia.com/gpu`, `cpu`, `memory`)가 컨테이너 resource key, 수량이 request/limit.
3. **type=Node**: `node.nodeSelector`/`tolerations` → pod에 직접 주입.
4. **type=Queue**: pod에 placement 안 넣고 `localQueueName` 큐에 제출 → **실제 노드 배치·toleration은 Kueue 큐(ResourceFlavor)가 결정**. priorityClass는 WorkloadPriorityClass로.

## 5. NVIDIA GPU Operator vs RHOAI 경계 (★3단 분업)
- **NFD**: 노드 하드웨어 탐지·라벨링(`NodeFeatureDiscovery` CR). 별도 설치.
- **NVIDIA GPU Operator**: driver + device plugin + MIG manager + time-slicing 관리(`ClusterPolicy` CR). 별도 설치. → `nvidia.com/gpu` 등 확장 리소스 **공급**.
- **RHOAI (HardwareProfile)**: 공급된 리소스를 **소비만**. 분할(MIG/time-slicing) 활성화엔 관여 안 함.

## 6. HardwareProfile vs Kueue 쿼터 (★별개)
| 축 | HardwareProfile | Kueue |
|---|---|---|
| 단위 | **per-pod 요청 + 배치** | **집계 쿼터 + admission** |
| 정의 | identifiers(양 min/max), scheduling(placement) | ClusterQueue/LocalQueue/ResourceFlavor(총량 한도) |
| 관계 | `scheduling.kueue.localQueueName`으로 큐 **참조만** | 쿼터 수치 자체 보유 |
| 독립 | type=Node면 Kueue 없이 단독 동작 | type=Queue에서만 연결 |

→ "이 워크로드가 무엇을·어디에"(HardwareProfile)와 "총량 한도 내 언제 admit"(Kueue)는 분리. dashboard `disableKueue` 기본 true. → [21-Kueue](21-Kueue.md)

## 7. MIG / time-slicing 소비
- 구성은 GPU Operator 측(time-slicing은 `time-slicing-config` ConfigMap + `ClusterPolicy.spec.devicePlugin.config`, replicas배 광고).
- RHOAI 소비: HardwareProfile identifier에서 `nvidia.com/gpu` 1 요청 → 슬라이스 1 획득. MIG는 device plugin이 `nvidia.com/mig-1g.5gb` 등 별도 리소스명 노출 → identifier를 해당 MIG명으로 지정(추정).
- 상세 전략: `../../../5-RHOAI-Delivery-Insights/GPU-공유전략-MIG-MPS-Timeslicing`

## 8. 운영 함정
- **CEL 상호배타**: type=Queue인데 `node` 넣거나 반대면 admission 거부. type=Queue면 `localQueueName` 필수.
- **Queue 모드에서 nodeSelector 무의미**(ResourceFlavor가 결정).
- NFD/GPU Operator 미설치/순서: 없으면 `nvidia.com/gpu` 미노출 → 스케줄 불가.
- 신규는 AcceleratorProfile 말고 HardwareProfile.

## 9. 출처
- 소스: `opendatahub-io/opendatahub-operator` (api/infrastructure/v1/hardwareprofile_types.go)
- RHOAI 3.4 working_with_accelerators / managing_resources

## 10. 미확인/주의
- GA 전환 마이너 버전, AcceleratorProfile 완전 removal, MIG를 HardwareProfile로 소비하는 공식 예제.
