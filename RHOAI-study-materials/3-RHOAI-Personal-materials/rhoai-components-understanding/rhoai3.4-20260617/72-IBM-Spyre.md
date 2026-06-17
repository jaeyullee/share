# IBM Spyre Operator

> IBM Spyre AI Accelerator(AIU)를 OpenShift AI 서빙에 통합하는 오퍼레이터. device plugin·secondary scheduler·monitoring 설치 자동화.
> 영역: [70-가속기데이터UI-관계](70-가속기데이터UI-관계.md)

---

## 1. 정의 / 역할
- IBM Spyre = IBM Research AIU 첫 production-grade AI 가속기. Spyre Operator가 "Spyre를 OpenShift AI workflow에 직접 통합".

## 2. 버전 / 라이프사이클
- 업스트림 `vllm-project/vllm-spyre`(= SenDNN Inference, vLLM 플러그인). 컨테이너 `quay.io/ibm-aiu/sendnn-inference`.
- **라이프사이클(플랫폼별)**:
  - **x86 = Technology Preview**(SLA 없음).
  - **IBM Z(s390x) / Power(ppc64le) = GA 추정/미확인**(이들엔 TP 문구 없음 근거의 추정, "GA" 직접 인용 미확인).

## 3. 아키텍처 / 설치
- 필수 동반 Operator 4종: **IBM Spyre Operator + NFD + cert-manager + Secondary Scheduler Operator**.
- 워커 노드: RAM 512GB+, 로컬 디스크 500GB+, MachineConfig 적용.
- 설치 후 `SpyreClusterPolicy` CR 생성. 기본 스케줄러 사용 시 `spec.experimentalMode.externalDeviceReservation` 제거.

## 4. CRD
- **`SpyreClusterPolicy`** — Spyre Operator 핵심 CR(전체 스키마는 IBM 문서, 미확인).
- `NodeFeatureDiscovery` — NFD CR(전제).

## 5. 서빙 경로 (★KServe ServingRuntime 통합)
플랫폼별 3개 ServingRuntime 템플릿:

| 플랫폼 | ServingRuntime |
|---|---|
| x86 | vLLM Spyre AI Accelerator ServingRuntime for KServe |
| IBM Z (s390x) | vLLM Spyre s390x ServingRuntime for KServe |
| IBM Power (ppc64le) | vLLM Spyre ppc64le ServingRuntime for KServe |

End-to-end: Spyre Operator+동반 설치 → `SpyreClusterPolicy` → **Spyre용 HardwareProfile 구성**(전제) → 아키텍처별 vLLM Spyre ServingRuntime 선택 → **KServe InferenceService로 single-model serving**. 리소스 식별자: `ibm.com/spyre_pf`, `ibm.com/spyre_pf_tier0/1/2`.

> 명명 불일치 주의: upstream(docs.vllm.ai v2.0.0)은 구명칭 `ibm.com/aiu_pf`/`aiu-scheduler`/developer preview. RHOAI 3.4 GA 문서는 `spyre_pf`/`SpyreClusterPolicy`로 리브랜딩(전환 중 추정).

## 6. 연동
- **HardwareProfile**: Spyre 서빙의 명시적 전제(가속기 리소스 매핑) → [71-GPU-하드웨어프로필](71-GPU-하드웨어프로필.md).
- **KServe**: ServingRuntime/InferenceService 통합 → [31-KServe](31-KServe.md).
- **NFD**: GPU와 동일하게 탐지/라벨링 전제.

## 7. 운영 함정
- x86 TP(SLA 없음). 하드웨어 요구 큼(512GB RAM/500GB 디스크). 의존 Operator 다수로 설치 복잡.
- RHOAI 문서가 자체 완결적이지 않고 IBM 외부 문서 위임.
- 미지원: LoRA, Speculative Decoding, Pipeline/Expert/Data Parallel, encoder-decoder.
- upstream↔RHOAI 명명 혼동.

## 8. 출처
- 업스트림: https://github.com/vllm-project/vllm-spyre , docs.vllm.ai/projects/spyre
- RHOAI 3.4 deploying_models / working_with_accelerators

## 9. 미확인/주의
- s390x/ppc64le 정확 lifecycle(GA 직접 인용), `spyre_pf_tier0/1/2` 정의, SpyreClusterPolicy 전체 스키마.
