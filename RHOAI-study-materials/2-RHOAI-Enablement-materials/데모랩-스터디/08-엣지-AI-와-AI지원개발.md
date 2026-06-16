# 엣지 AI 파이프라인 & AI 지원 개발 (enabler)

> 응용 시나리오 두 개: `sp-edge-to-cloud-data-pipelines`(#7) + `ai-assisted-development`(#10).
> "RHOAI/LLM을 실제 워크플로우 어디에 붙이나"의 두 사례.
> 연결: [[03-rhoai-mlops-knowledge]], [[03-MCP-핵심]]

---

# A. 엣지↔클라우드 모델 피드백 루프 (#7)

## A1. 무엇을 보여주나
엣지에서 이미지 수집·추론 → 중앙으로 데이터 전송 → 재학습 → 최신 모델을 엣지로 재배포하는 **완전한 MLOps 순환 루프**의 인프라 구현.

## A2. 흐름
```
[IoT] --MQTT/HTTP--> [엣지존: AMQ Broker + Camel(Quarkus) + TF Serving + Minio + edge-manager]
   (1) 추론결과+학습데이터 → 중앙 Minio(edge1-data)
   (2) 신규모델 폴링 ← 중앙 Minio(production)
        ↕ Service Interconnect(보안터널)
[중앙: Minio + central-feeder + Kafka(AMQ Streams) + Camel K(delivery) → Tekton Pipeline(학습/검증/푸시)]
```

## A3. 핵심 기술·포인트
- **엣지 추론**: TF Serving 로컬 호스팅 → 레이턴시↓·네트워크 의존↓.
- **이벤트 기반 재학습**: Kafka 트리거 → Camel K → Tekton Pipeline. 느슨한 결합(비동기).
- **모델 버전관리**: S3/Minio 기반 교환, 엣지가 신규모델 폴링·자동 로드(무중단 업데이트).
- **Service Interconnect**: 다중 엣지존↔중앙 프라이빗 터널. 각 존 독립 네임스페이스.
- **데이터 주권**: 엣지에서 필터링 후 필요한 것만 중앙 전송(개인정보·대역폭).
- **확장**: Ansible(`-e EDGE_NAME=zone2`)로 엣지존 수평확장, 중앙 단일 파이프라인이 전 존 학습/배포.

## A4. enabler 메시지
- RHOAI는 "모델 학습/등록"을, 통합(Camel/AMQ)·파이프라인(Tekton)·엣지(TF Serving)와 엮어 **MLOps 피드백 루프**로 완성. RHOAI 단독이 아니라 OpenShift 통합 제품군 스토리.
- 제조/리테일/통신 엣지 시나리오 영업에 유효. RHOAI Model Registry로 모델 버전관리 가능.

---

# B. AI 지원 개발 루프 (#10)

## B1. 무엇을 보여주나
vLLM(Mistral) 배포 → IDE(Continue) 코드생성 → GitLab CI에서 SonarQube + AI 에이전트가 **자동 코드리뷰** → MR 댓글까지 엔드투엔드 "shift-left" 품질 루프.

## B2. 흐름
```
개발자 → Continue(IDE, 실시간 완성) → GitLab Push/MR
  → GitLab CI: build → SonarQube 정적분석 → ai-suggestion 에이전트 호출
       (SonarQube 이슈 조회 → LLM(Mistral) 수정제안 요청 → GitLab MR 댓글 작성)
  → 개발자(MR에서 AI+Sonar 제안 확인) → 수정·재커밋 → 통과 → Merge
  → GitLab Reviewer 대시보드(팀 전체 MR 통합관리)
```

## B3. 핵심 기술·포인트
- **서빙**: KServe/vLLM Mistral-7B(OpenAI 호환), MinIO 모델 저장소, **토큰 인증**, L4 GPU 1장.
- **IDE**: Continue 플러그인 — 완성, 슬래시 커맨드(/edit /comment /test /commit), 컨텍스트 프로바이더(Code/Docs/Diff/Terminal/Problems/Codebase). `~/.continue/config.json`에 `apiBase`+`apiKey`.
- **AI 에이전트**: `ai-suggestion` 마이크로서비스(Python) — ConfigMap에 LLM/SonarQube/GitLab 토큰. CI 변수(`CI_MERGE_REQUEST_IID`, `PROJECT_KEY`)로 트리거. SonarQube 실패해도 `|| true`로 제안 지속.
- **OpenAI 호환의 가치**: Continue·Open WebUI·ai-suggestion이 커스텀 없이 즉시 연동.

## B4. enabler 메시지
- "RHOAI는 LLM 배포 도구가 아니라 **MLOps 플랫폼**" — KServe 프로덕션 서빙 + Workbench + 토큰/GPU 관리.
- MinIO 모델 저장소(RHOAI는 저장소 아님) + Data Connection 연결 패턴 필수.
- 개발팀/DevEx 고객에게 "AI가 코드작성→검토→개선을 자동화"하는 구체적 ROI 시연.
- GPU 제약 현실: L4 1장=Mistral 1모델. 프로덕션은 멀티 GPU·레플리카 전략 → [[0-Important/03-RHOAI-워커노드-리소스-산정법]].
