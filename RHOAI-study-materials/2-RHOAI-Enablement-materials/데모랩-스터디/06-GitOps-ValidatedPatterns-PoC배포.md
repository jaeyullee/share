# GitOps · Validated Patterns · PoC 배포 (enabler)

> `rag-llm-gitops`(#6) + `genai-rhoai-poc-template`(#11) + 부분적으로 `edge`(#7)에서 추출.
> "RHOAI AI 스택을 어떻게 코드로·반복가능하게 배포하나"에 초점.
> 연결: [01-RHOAI3-신규기능-핵심](01-RHOAI3-신규기능-핵심.md), [05-RAG-데모관점-정리](05-RAG-데모관점-정리.md)

---

## 1. Validated Patterns 란

- Red Hat의 **검증된 레퍼런스 아키텍처를 코드로** 제공하는 프레임워크. 고객 PoC를 빠르게 재현·시연하는 무기.
- 구조: `pattern-metadata.yaml`(메타) + `pattern.sh`(자동화) + `charts/`(Helm) + `ansible/`(부트스트랩).
- 설정 분리:
  - `values-global.yaml` — DB 타입, 모델, 스토리지클래스, ArgoCD 동기화 정책 등 전역.
  - `values-secret.yaml` — HF 토큰·구독토큰 등 민감정보 외부화(Vault 통합), Git에 안 올림.
- **`make install` 한 번**(데모 기준 15~20분)으로 전체 스택 자동 배포.

---

## 2. GitOps 배포 흐름 (rag-llm-gitops #6)

1. Ansible이 OCP에 ArgoCD 설치 + Pattern CRD 배포(부트스트랩).
2. `values-global.yaml`에서 DB(PGVECTOR/EDB/REDIS/…)·모델·GPU 인스턴스 선택 → 해당 리소스만 Helm 배포.
3. **GPU MachineSet 자동 생성**: `./pattern.sh make create-gpu-machineset` → AWS g5.2xlarge MachineSet(taint/label 자동) → NVIDIA GPU Operator + NFD가 감지.
4. `./pattern.sh make install` → ArgoCD ApplicationSet이 vLLM·벡터DB·앱(Gradio)·모니터링·RAG 적재 Job을 선언적으로 동기화.
5. 이후 Git 변경 → ArgoCD 자동 동기화(재배포 없이 모델/제공자 동적 추가).

> OCP 비유: "환경 = Git". 클러스터 상태를 ArgoCD가 Git과 지속 동기화. 드리프트 자동 교정.

---

## 3. PoC 템플릿 흐름 (genai-rhoai-poc-template #11)

- **3단계 게이팅 배포**(ApplicationSet + Kustomize, 각 단계는 이전 완료 대기):
  1. **First**: MCGW(ODF Multi-Cloud Gateway, S3) + RHOAI(DataScienceCluster) 설치, Workbench 이미지 사전로드.
  2. **Model Synchronization**: `model-source` Secret을 **대기** → 사용자가 모델 소스 지정 → s3cmd Job이 `models/` 동기화.
  3. **Last**: KServe/vLLM + Authorino(토큰인증) 모델 배포 → AnythingLLM(RAG UI, KServe 엔드포인트 자동연결) → 평가 준비.
- 모델 입력 3방식: ① 자동(in-cluster s3cmd) ② CLI 반자동(`upload.sh`+podman) ③ GUI(ODH TEC 드래그앤드롭).
- 런타임 아키텍처: `AnythingLLM → (vLLM 엔드포인트 / Milvus 벡터DB) → MCGW S3(모델·인덱스)`.
- **Data Connection CRD**로 S3 버킷을 Workbench에 네이티브 마운트.

---

## 4. #6 vs #11 — 언제 무엇을

| | rag-llm-gitops (#6) | genai-poc-template (#11) |
|---|---|---|
| 성격 | 공식 **Validated Pattern**(정석) | 가벼운 **PoC 부트스트랩**(rh-aiservices-bu) |
| 배포 | `make install`, ArgoCD ApplicationSet | ArgoCD + Kustomize 3단 게이팅 |
| 벡터DB | pgvector/EDB/Redis/ES/MSSQL 선택 | Milvus(+Attu) |
| UI | Gradio | AnythingLLM |
| 강점 | 멀티제공자 A/B 평가, 검증된 구조 | 모델 입력 유연성, 빠른 맞춤 PoC |
| 추천 | 레퍼런스·시연·표준화 | 고객 맞춤 빠른 PoC |

---

## 5. 공통 인프라 의존성 (둘 다 필요)

- NVIDIA GPU Operator + Node Feature Discovery(GPU 감지·라벨).
- S3 호환 스토리지(MCGW/ODF 또는 MinIO) — RHOAI 자체는 모델 저장소 아님.
- KServe + vLLM(OpenAI 호환), Authorino(토큰 인증).
- (선택) OpenShift Serverless(Knative) + Service Mesh(Istio) — KServe 서빙 기반.

---

## 6. enabler 핵심 메시지

- "PoC를 손으로 깔지 말고 **코드로**" — 재현성·롤백·고객 이관이 쉬워진다.
- Secret 외부화(values-secret/Vault)는 기본. Git에 토큰 올리면 사고.
- GPU MachineSet 자동생성은 클라우드(AWS) 전제 — 온프레는 노드 사전준비 필요.
- 고객 PoC 시작 시: #11로 빠르게 띄워 가치 증명 → #6(Validated Pattern)으로 표준화/확장.
- 배포 검증 루틴: 네임스페이스별 Pod(vLLM/벡터DB/UI/모니터링) Ready, GPU 할당(`nvidia.com/gpu`), Route 접근, 적재 Job 완료.
