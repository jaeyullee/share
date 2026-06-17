# MCP (Model Context Protocol) 핵심 (enabler 관점)

> `lb1726-mcp-showroom`(#8) + `llamastack-on-ocp`(#4) + `agentic-ai-llamastack`(#5) + `llmaas`(#2)에서 추출.
> 연결: [02-Llama-Stack-핵심](02-Llama-Stack-핵심.md), [04-에이전트-AI-패턴](04-에이전트-AI-패턴.md), [02-AI-에이전트-도구호출-프롬프트패턴](../../4-etc-AI-materials/02-AI-에이전트-도구호출-프롬프트패턴.md)

---

## 1. 한 줄 정의

**MCP = AI 에이전트와 외부 시스템(인프라·DB·이슈트래커·메시징)을 잇는 표준 프로토콜.** 시스템마다 커스텀 통합 코드를 짜는 대신, 모든 AI 앱이 **단일 인터페이스**로 외부 도구를 발견·호출한다.

> 비유: LLM 세계의 "USB-C" 또는 "ODBC". 도구(시스템)마다 다른 어댑터를 짤 필요 없이 표준 포트로 꽂는다.

---

## 2. 구성 요소

| 요소 | 역할 |
|---|---|
| **MCP 서버** | 외부 시스템을 감싸 **도구(tools)**로 노출 (예: OpenShift MCP=23 도구, Gitea MCP=106 도구) |
| **MCP 클라이언트** | 도구를 발견·호출하는 쪽 (LibreChat, Llama Stack 에이전트, RHOAI 에이전트 런타임) |
| **도구(tool)** | 서버가 제공하는 개별 기능 + 메타데이터(이름/설명/파라미터) |
| **ToolHive** | stdio 기반 MCP 서버를 HTTP로 브리징 → OCP에 분산 배포. 단순 스크립트도 MCP 서버화 |
| **MCPToolConfig (CR)** | 도구 필터링(allowlist) = 최소권한 접근제어 |
| **MCP Registry** | 조직 전체 MCP 서버 중앙 카탈로그·승인·감사 |

---

## 3. 에이전트가 도구를 쓰는 흐름

1. 클라이언트가 서버에 연결 → 서버가 제공 도구 목록·메타데이터 **발견(discovery)**.
2. LLM이 사용자 요청을 보고 "어떤 도구를, 어떤 파라미터로" 호출할지 **자율 결정**.
3. 도구 실행 → 결과를 다시 LLM에 관찰값으로 전달 (ReAct 루프와 결합).
4. 메타데이터 기반이라 **코드 변경 없이** 새 도구 추가/제거 가능(동적 적응).

---

## 4. 대표 시나리오 (데모)

- **Sovereign SRE 에이전트(#8)**: 파이프라인 실패 → OpenShift MCP로 로그 조회 → 근본원인 분석 → Gitea MCP로 이슈 자동 생성. CLI 안 외우고 자연어로 인프라 질의.
- **자동 인시던트 대응(#4 Level 6)**: 분석 → 문서검색(RAG) → 인프라 상태조회(MCP) → 해결안 → Slack 보고.
- **운영 자동화(#2)**: "메모리 부족 pod 찾아줘" → Kubernetes MCP가 쿼리 → Slack MCP가 알림.
- **엔터프라이즈 백엔드(#5)**: Customer/Finance MCP 서버(포트 8001/8002)를 FastAPI 위에 얇게 씌워 비즈니스 도구화.

---

## 5. 거버넌스·보안 (enabler가 처음부터 설계할 것)

- **최소권한(allowlist)**: `MCPToolConfig`로 에이전트별 가용 도구 제한. 예) 개발 에이전트는 "프로덕션 삭제" 도구 안 보임, SRE 에이전트는 인프라 도구만.
- **감사·모니터링**: Prometheus/ServiceMonitor로 "어느 에이전트가 어떤 도구를 얼마나 호출했나" 추적 → 이상행동 탐지.
- **GitOps 관리**: ArgoCD로 서버 배포·도구 설정·권한을 코드로 → 변경이력·롤백.
- **MCP Registry**: 서버 상태(Official/Community/Experimental, Active/Deprecated) + 보안팀 승인 워크플로우 → 조직 AI 도구 인벤토리·감사 완성.
- 다음 단계(데모 언급): **OAuth 2.0** 인증, 커스텀 서버(내부 API 래핑), 멀티환경 배포.

---

## 6. "MCP를 얇은 어댑터로" 패턴 (★중요)

기존 REST API/마이크로서비스를 **재작성하지 말고** MCP 메타데이터로 감싸기만 한다. 비즈니스 로직은 그대로, 도구 정의(메타데이터)만 추가 → AI 에이전트가 즉시 사용. 이게 엔터프라이즈 통합의 핵심 셀링포인트.

---

## 7. enabler 핵심 메시지

- MCP는 "도구를 더 주는 것"이 아니라 **LLM을 시스템의 자동화 의사결정 엔진으로 만드는 표준 계층**.
- RHOAI 에이전트 솔루션 = (Llama Stack/LangGraph 에이전트) + (MCP 서버들) + (거버넌스: MCPToolConfig/Registry/모니터링).
- 고객 PoC 설계 시 3종 세트 먼저 결정: ① 어떤 시스템을 MCP로 노출? ② 에이전트별 도구 권한(allowlist)? ③ 감사/모니터링 방식?
- 입문 실습: lb1726-mcp-showroom(#8)이 거버넌스 중심, llamastack-on-ocp(#4) Level 5~6이 개발 중심.
