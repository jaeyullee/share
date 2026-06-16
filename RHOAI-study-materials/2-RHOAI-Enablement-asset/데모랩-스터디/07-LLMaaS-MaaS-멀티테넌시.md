# LLMaaS / MaaS · 멀티테넌시 · 과금 (enabler)

> `llmaas-showroom`(#2) + RHOAI 3 MaaS(#3) + 게이트웨이(RHCL)에서 추출.
> "LLM을 조직의 공용 서비스로 운영"하는 Platform Engineering 관점.
> 연결: [[01-RHOAI3-신규기능-핵심]], [[06-Models-as-a-Service-가이드]]

---

## 1. LLMaaS vs MaaS

- **LLMaaS** = 조직 내부에서 LLM을 **중앙 서비스**로 제공(여러 팀이 공용 GPU·모델 사용). 운영/문화 관점.
- **MaaS (Models-as-a-Service)** = 그걸 **구독형 제품**으로 만드는 RHOAI 3 기능(게이트웨이+과금+카탈로그). 제품 관점.
- 핵심 가치: 팀마다 GPU 사고 모델 깔지 말고 → **중앙 풀링**으로 유휴율↓·비용↓·거버넌스↑.

---

## 2. 4대 역량 (llmaas 데모 결론)

1. **Deployment** — Foundation Model을 클러스터에 배포(OpenShift AI 대시보드).
2. **Scalable Service Exposure** — 엔드포인트 노출 + 토큰 인증, OpenAI 호환 API.
3. **Workflow Integration** — 개발자(Continue/Dev Spaces) + 운영 자동화(Llama Stack+MCP 에이전트).
4. **Observability** — 토큰 소비·사용자별/계층별 비용·용량계획(Prometheus/Grafana).

---

## 3. 멀티테넌시 설계

- **네임스페이스 격리**: Platform 팀이 모델 관리, 개별 팀은 토큰으로 접근. 모델은 **클러스터 내부에만 노출**(보안 우선).
- **토큰 기반 인증/인가**: Authorino(인증) + Limitador(rate limit)로 게이트웨이에서 제어 → [[01-RHOAI3-신규기능-핵심]] §5.
- **엔드포인트 추상화**: OpenAI 호환 인터페이스 → 뒤의 모델 교체 자유(provider 독립).
- **GitOps 배포**: ArgoCD로 모델 라이프사이클을 선언적으로 관리.

---

## 4. 과금 / 비용 추적

- **토큰 단위 과금**: 토큰 수 × 계층별 단가. 사용자/팀별 청구.
- Grafana 대시보드: "Top 5 Users by Cost", 시계열 토큰 소비 → 용량계획·스케일링 의사결정.
- GPU 풀링으로 자본 효율(여러 모델이 공유 GPU). → [[GPU-공유전략-MIG-MPS-Timeslicing]]

---

## 5. 개발자 경험 (DevEx)

- **Continue**(VS Code 확장) + **Dev Spaces**(클라우드 IDE)로 모델에 네이티브 접근 — 외부 노출 최소화.
- `apiBase` + 토큰만 넣으면 코드 작성/리팩토링/테스트 생성에 LLM 활용.
- 운영 자동화: Llama Stack 에이전트 + Kubernetes/Slack MCP로 자연어 클러스터 진단·알림. → [[03-MCP-핵심]]

---

## 6. 데이터 흐름 요약

```
Platform 팀(배포·GitOps)
  → OpenShift AI(중앙 모델 서버, vLLM)
  → [게이트웨이: Authorino 인증 + Limitador rate limit + TLS]
  → 개발자(Continue/Dev Spaces) / 운영 에이전트(Llama Stack+MCP)
  → Prometheus/Grafana(토큰·비용·성능 추적)
```

---

## 7. enabler 핵심 메시지

- LLMaaS의 셀링포인트: "GPU·모델 중복 투자 제거 + 보안(내부 노출) + 비용 가시성(과금)".
- RHOAI 3의 MaaS 기능(게이트웨이/과금)은 데모 기준 일부 WIP → 고객 환경 GA 버전 기능 확인.
- 고객 질문 대비: 테넌트 격리 수준, rate limit 정책, 토큰 발급/회수, 비용 배분 모델, 모델 카탈로그 거버넌스.
- 더 상위 비즈니스 자료: [[06-Models-as-a-Service-가이드]], [[02-Red-Hat-AI-플랫폼-고객덱]].
