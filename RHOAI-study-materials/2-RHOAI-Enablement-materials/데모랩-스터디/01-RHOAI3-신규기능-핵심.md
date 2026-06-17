# RHOAI 3.0 신규 기능 핵심 (enabler 관점)

> `redhat-openshift-ai-3-showroom`(데모 #3) + `llm-d-showroom`(#1)에서 추출.
> RHOAI 2.x를 알던 사람이 3.0에서 **무엇이 바뀌었나**를 빠르게 잡는 노트. 일부는 데모 기준 "alpha/WIP"이므로 GA 시점에 재확인 필요.
> 기반: [02-OpenShift-AI-플랫폼-아키텍처](../../3-RHOAI-Personal-materials/02-OpenShift-AI-플랫폼-아키텍처.md), [01-RHOAI-기초-용어정리](../../3-RHOAI-Personal-materials/01-RHOAI-기초-용어정리.md)

---

## 1. 가장 큰 변화 한 줄 요약

RHOAI 3는 **"GenAI/추론 플랫폼"으로 무게중심 이동**이다. 전통 MLOps(노트북·파이프라인·실험)는 그대로 있되, **vLLM 기본 서빙 + llm-d 분산추론 + MaaS(게이트웨이/과금) + LlamaStack/GenAI Playground + MCP**가 1급 시민으로 들어왔다. OCP 엔지니어 비유로: 2.x가 "쿠버네티스 위 데이터과학 워크벤치"였다면, 3.0은 "쿠버네티스 위 **모델 추론 서비스 메시 + API 게이트웨이**"가 추가된 느낌.

---

## 2. DataScienceCluster v2 — 단일 CRD로 컴포넌트 토글

- API: `datasciencecluster.opendatahub.io/v2`. **하나의 CR**에서 모든 AI 컴포넌트 라이프사이클을 선언적으로 관리.
- 각 컴포넌트는 `Managed`(설치·운영) / `Removed`(미설치) 상태로 토글. 필요한 것만 켠다.
- 관리 대상(데모 확인): Workbenches, KServe, vLLM, **Model Registry**, Pipelines, **Feature Store Operator**, **LlamaStack Operator**, Ray, Training Operator, TrustyAI, (Kueue는 데모에서 Removed로 표시 — 버전별 상태 변동 주의).

> OCP 비유: Operator의 `spec.components.*.managementState`로 기능을 On/Off 하는 패턴. 설치=DSC에 컴포넌트 추가, 제거=Removed. GitOps로 관리하기 좋음.

**검증 흐름**: Operator 설치 → DSC 배포 → Pod/CRD Ready 확인. UI보다 **YAML/GitOps 권장**(복잡한 CRD는 UI 배포 시 실패 표시 가능).

---

## 3. 모델 서빙 — vLLM이 KServe 1순위 런타임

- vLLM ServingRuntime이 **표준**. NVIDIA GPU(CUDA) 가속 LLM 서빙의 기본값.
- 모델 온보딩 3단계 표준화: **Secret(OCI/S3 모델 위치) → ServingRuntime(vLLM 정의) → InferenceService(KServe+GPU 프로파일)**. 자동화/스크립트화 쉬움.
- Red Hat 모델 레지스트리/카탈로그에서 사전 최적화 모델(FP8 등) 사용 가능. 예: Llama 3.1 8B FP8, Llama 3.2 3B Instruct.
- **하드웨어 프로파일**: Workbench/InferenceService가 명시적 GPU 프로파일 선택(NodeSelector + 리소스 쿼터 예 1 GPU/4 CPU/16Gi). 멀티 GPU 타입 환경에서 모델별 최적 배정. → [[GPU-공유전략-MIG-MPS-Timeslicing]]

---

## 4. llm-d — 분산추론 게이트웨이 (캐시 인식 라우팅)

- `LLMInferenceService` CR이 다수 vLLM 인스턴스를 오케스트레이션.
- **3개 스코어러**로 라우팅 결정: `prefix-cache-scorer`(KV 캐시 매칭 최대화), `queue-scorer`(큐 깊이 균형), `active-request-scorer`(활성 요청). 가중치 조정 가능(데모 예 3/2/2).
- 효과: 동일 4 레플리카에서 round-robin 대비 **캐시 히트율 20~30%→60~80%**, **TTFT p95 24s→478ms**.
- 핵심 인사이트: **GPU 추가(throughput↑) ≠ tail latency 개선**. 반복 prefix(시스템 프롬프트·공유 문서·멀티턴) 워크로드일수록 캐시 인식 라우팅 이득이 큼.
- 측정 도구: GuideLLM(KV 캐시 인식 벤치마크), Grafana 지표 `vllm:num_requests_running`, `vllm:kv_cache_usage_perc`, TTFT/ITL.

→ 깊은 내용은 [01-분산추론과-llm-d](../../3-RHOAI-Personal-materials/read/01-분산추론과-llm-d.md), 벤치마킹은 [06-LLM-벤치마킹-GuideLLM-가이드](../../4-etc-AI-materials/read/06-LLM-벤치마킹-GuideLLM-가이드.md).

---

## 5. RHCL 기반 Inference Gateway (LLMd 배포)

- **RHCL(Red Hat Connectivity Link)** Operator + **Gateway API**(GatewayClass/Gateway) 기반 통합 API 게이트웨이.
- 구성요소: RHCL + DNS + **Limitador**(rate limit) + **Authorino**(인증/인가). HTTPS/TLS 터미네이션, 네임스페이스 격리.
- 의미: 추론 엔드포인트의 인증·속도제한·TLS를 **단편적이 아니라 통합 정책**으로. 기업용 API 관리(API Gateway) 패턴이 RHOAI에 내장.

> OCP 비유: Route/Ingress 단순 노출을 넘어, "API Gateway(인증+rate limit+TLS)"를 Gateway API CR로 선언. Authorino=인증 사이드카, Limitador=토큰 버킷 rate limiter.

---

## 6. MaaS (Models as a Service) — ODH MaaS 기반

- 모델을 **구독형 서비스**로: 토큰 단위 과금, 사용자/팀별 비용 추적, 게이트웨이를 통한 접근.
- 5번 게이트웨이(Authorino/Limitador) + 관찰성(토큰 소비 메트릭)과 결합.
- 데모 기준 일부 WIP. 상세는 [07-LLMaaS-MaaS-멀티테넌시](07-LLMaaS-MaaS-멀티테넌시.md).

---

## 7. GenAI Playground + LlamaStack 자동화

- 모델을 "Add to Playground" 하면 **LlamaStackDistribution 인스턴스 + ConfigMap(run.yaml) + Pod이 자동 생성** → 원클릭 대화형 테스트 환경.
- LlamaStack Operator가 DSC 관리 컴포넌트로 포함. → [02-Llama-Stack-핵심](02-Llama-Stack-핵심.md)
- ODH Dashboard에 GenAI 스튜디오·모델 카탈로그·MaaS·KServe 메트릭이 **단일 UI로 통합**.

---

## 8. Model Registry 네임스페이스 격리

- Model Registry가 `rhoai-model-registries` 네임스페이스에서 중앙 관리. OCI 모델 저장소 통합.
- 멀티테넌트에서 모델 검색·공유·버전관리의 보안/거버넌스 강화. → [03-rhoai-mlops-knowledge](../../3-RHOAI-Personal-materials/03-rhoai-mlops-knowledge.md)

---

## 9. 관찰성 의무화 + 거버넌스(TrustyAI)

- **Cluster Observability Operator**로 메트릭 수집 표준화. KServe 추론 메트릭·모델 성능을 대시보드에서 즉시 가시화.
- **TrustyAI** 기본 컴포넌트: 모델 설명성(SHAP/LIME 계열)·편향 탐지. AI 규제(공정성) 대응.

---

## 10. 분산 학습 스택 확장

- **Training Operator + Ray**로 단일노드 학습→클러스터 분산학습 수평확장. PyTorch/TF 분산 작업 통합.
- (Kueue 워크로드 큐는 버전별 포함/제외 상태 변동 — 실제 DSC에서 확인) → [04-GPU-인프라-MIG-슬라이싱-Kueue](../../3-RHOAI-Personal-materials/04-GPU-인프라-MIG-슬라이싱-Kueue.md)

---

## 11. enabler 체크리스트 (RHOAI 3 시연/설치 전)

- [ ] GPU 노드/드라이버 준비 (NVIDIA GPU Operator + NFD), 하드웨어 프로파일 정의
- [ ] DSC에서 켤 컴포넌트 선택 (서빙 중심이면 KServe/vLLM/llm-d/LlamaStack, 전통 MLOps면 Pipelines/Workbench/Training)
- [ ] 게이트웨이 필요 여부 (외부 노출·과금이면 RHCL+Authorino+Limitador)
- [ ] 모델 소스 (OCI 레지스트리 / S3) 와 Secret 구성
- [ ] 관찰성(Cluster Observability Operator) + Grafana 대시보드
- [ ] YAML/GitOps로 배포 (UI 배포 실패 회피)
- [ ] 버전 캐비엇: 데모 일부 alpha/WIP → 고객 환경 GA 버전 기준으로 기능 가용성 재확인

---

## 한 줄 메모

RHOAI 3 시연의 "와우 포인트" 3개: ① llm-d 캐시 라우팅 전후 TTFT 비교 그래프, ② GenAI Playground 원클릭 모델 테스트, ③ RHCL 게이트웨이로 토큰 발급→과금 대시보드. 이 셋이 "추론 플랫폼으로서의 RHOAI 3"를 가장 잘 보여준다.
