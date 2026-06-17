# AI Hub (AI Available Assets + MCP Catalog)

> RHOAI dashboard 최상위 "엔터프라이즈 GenAI command center". 대부분 dashboard 레이어이나 MCP 배포는 별도 operator 의존.
> 영역: [60-GenAI평가안전-관계](60-GenAI평가안전-관계.md)

---

## 1. AI Hub 정의 / 역할
- ODH dashboard 최상위 메뉴. 하위: **Catalog(=Model Catalog), Model Registry, Deployments, Available Assets(신규), MCP Catalog(신규)**.
- AI Hub ⊃ Model Catalog. 골격/Catalog/Registry/Deployments는 GA.

## 2. AI Available Assets (프리뷰, TP/DP 미확정)
- 선택 **프로젝트(namespace) 범위**의 배포된 모델 엔드포인트 + MCP 서버를 조회/소비하는 필터형 UI.
- **MaaS**(3.4 GA) 엔드포인트도 소비 대상. tool-calling 메타데이터 표면화. → [33-MaaS](33-MaaS.md)

## 3. MCP Catalog (DP)
- MCP 서버 큐레이션 카탈로그. 사전탑재 10종(Red Hat: OpenShift/Ansible AAP/Lightspeed; 파트너: Confluent/EDB Postgres/IBM Terraform/Azure/Dynatrace; OSS: MongoDB/MariaDB).
- 워크플로우 4단계: **Discover → Deploy(mcp-lifecycle-operator) → Connect(mcp-gateway) → Consume(gen AI studio)**.

### 아키텍처 (이중 구조)
UI는 dashboard 레이어지만 배포 백엔드는 별도 operator/CRD/gateway:
- **mcp-lifecycle-operator**(DP, v0.1.0): MCPServer 선언적 배포 → Deployment+Service+cluster-internal URL.
- **mcp-gateway**(TP): 여러 MCP 서버 tool을 **단일 엔드포인트로 집계**, identity-aware routing, per-tool metrics.
- (별개) **RHOAI MCP Server**(DP): Claude Code 등이 RHOAI를 자연어 제어 — 카탈로그와 혼동 주의.
- ⚠️ CRD 그룹 미확정: Red Hat 블로그=`mcp.x-k8s.io/v1alpha1` MCPServer vs upstream ToolHive=`toolhive.stacklok.dev/v1beta1`. `oc get crd | grep -i mcp`로 확인.

## 4. MCP ↔ Llama Stack
- MCP 서버는 Llama Stack `tool_runtime` provider(`remote::model-context-protocol`)로 등록, startup 시 자동 발견. mcp-gateway 단일 엔드포인트를 tool_runtime 대상 삼는 구성이 자연. MCP HTTP streaming(DP). → [61-Llama-Stack](61-Llama-Stack.md)

## 5. 동작 / 연동
- AI Hub는 **CRD 없는 dashboard 레이어**(Model Catalog·Registry·Deployments를 통합 뷰로). MCP 배포만 별도 operator.
- Available Assets에서 배포 모델 + MCP + MaaS를 프로젝트 단위로 소비.
- → [51-Model-Registry](51-Model-Registry.md), [52-Model-Catalog](52-Model-Catalog.md), [74-ODH-Dashboard](74-ODH-Dashboard.md)

## 6. 운영 함정
- AI Available Assets 라이프사이클 등급 미확정(TP/DP).
- MCP CRD 실제 그룹명 미확정 → 자동화 전 클러스터 확인.
- MCP Catalog는 순수 ConfigMap 아님(실제 CRD/operator 기반).

## 7. 출처
- AI Hub: https://www.redhat.com/en/blog/introducing-ai-hub-and-genai-studio-new-command-center-enterprise-generative-ai-red-hat-openshift-ai
- MCP Catalog: https://www.redhat.com/en/blog/mcp-catalog-here-discover-deploy-and-connect-red-hat-openshift-ai
- ToolHive(참고): https://github.com/stacklok/toolhive
