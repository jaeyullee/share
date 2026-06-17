# MaaS (Models-as-a-Service)

> 모델 서빙 인프라 **위에 얹는 거버넌스 레이어**. inference gateway로 토큰 인증·rate limit·사용량 추적(showback) 제공. 3.4 GA.
> 영역: [30-모델서빙-관계](30-모델서빙-관계.md)

---

## 1. 정의 / 역할
- 모델은 **LLMInferenceService**(llm-d/vLLM) 또는 외부 LLM 공급자 기반. MaaS는 그 앞단에서 **멀티테넌트 셀프서비스 + 과금·rate limit**을 enforce.
- 라이프사이클: **3.4 GA**(0.1.1). (단 vLLM runtime MaaS·외부 OIDC·관측 대시보드·외부 모델 egress는 3.4 TP)

## 2. 아키텍처 (게이트웨이 스택)
- **Red Hat Connectivity Link Operator 1.2+** (= **Kuadrant**, `kuadrant-system`).
- **Gateway API**: GatewayClass(`openshift.io/gateway-controller`) + Gateway `maas-default-gateway`(`openshift-ingress`).
- **Authorino** — 인증/인가. **Envoy proxy**(EnvoyFilter)로 Authorino와 TLS.
- **Kuadrant** — rate-limit/정책 enforcement. **User Workload Monitoring(Prometheus/Thanos)** — 사용량 메트릭.
- **PostgreSQL** — API 키 라이프사이클(`maas-db-config` secret).

## 3. CRD (group `maas.opendatahub.io/v1alpha1`)

| CRD | 역할 |
|---|---|
| **Tenant** | API 키 만료 한도, OIDC, 텔레메트리 설정 |
| **MaaSModelRef** | inference 서버 참조(LLMInferenceService/ExternalModel) |
| **MaaSSubscription** | 그룹 quota + `tokenRateLimits` |
| **MaaSAuthPolicy** | 그룹의 엔드포인트 접근 인가 |
| **ExternalModel** | 외부 LLM 공급자(OpenAI/Anthropic 등) |

(+ Gateway API의 GatewayClass/Gateway, EnvoyFilter)

## 4. 동작 / 인증 / rate limit
- **API 키**: `sk-oai-` 프리픽스. `POST /maas-api/v1/api-keys`. 영구/만료, 개별 폐기, 구독에 스코프. 인증 `Authorization: Bearer <token>`(API 키 또는 OIDC).
- **Rate limit**: `MaaSSubscription.tokenRateLimits[]{limit, window}`(window s/m/h, `d` 미지원). 모델당 최소 1개 필수. 그룹 단위.
- **메터링**: 구독별 토큰 소비/요청 수/위반 모니터링, CSV export(showback, **빌링 등급 아님**). `meteringMetadata`(organizationId/costCenter).
- **구독/그룹**: OpenShift 그룹 멤버십 기반. **priority**로 다중 구독 시 최고 우선순위 선택(Prod 100/Staging 50/Dev 0). **접근(MaaSAuthPolicy) + quota(MaaSSubscription) 둘 다 필요**.

## 5. 연동
- **MaaS는 LLMInferenceService를 `MaaSModelRef`로 publish**. 데이터 평면은 llm-d/KServe, MaaS는 앞단 게이트웨이(Kuadrant/Authorino)에서 인증·과금·rate limit. → [32-llm-d-분산추론](32-llm-d-분산추론.md)
- AI Hub의 AI Available Assets에서 MaaS 엔드포인트 소비 → [64-AI-Hub](64-AI-Hub.md).

## 6. 운영 함정
- Connectivity Link(Kuadrant)·Authorino·Gateway API 전제 — 설치 복잡.
- API 키에 PostgreSQL 필요. 구독 삭제 시 연관 키 무효화.
- rate limit window `d`(일) 미지원. showback ≠ billing-grade.

## 7. 출처
- MaaS govern 문서: docs.redhat.com 3.4 html-single/govern_llm_access_with_models-as-a-service/index
- 가이드: https://github.com/rh-aiservices-bu/rhoai-maas-guide
