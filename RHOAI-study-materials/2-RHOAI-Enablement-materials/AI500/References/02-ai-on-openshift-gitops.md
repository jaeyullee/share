# ai-on-openshift — GitOps

- **링크**: https://ai-on-openshift.io/odh-rhoai/gitops/
- **분류**: References (학습 자료)
- **한 줄**: RHOAI/ODH 설치·구성·워크로드를 Kubernetes 커스텀 리소스(YAML)로 GitOps 관리하는 방법.

## 핵심 개념

### 설치 레이어
- OLM의 `Subscription` 오브젝트로 RHOAI 오퍼레이터 배포
- `DSCInitialization` — ServiceMesh·신뢰 인증서 등 클러스터 전역 설정
- `DataScienceCluster` — 설치할 컴포넌트 지정 (`managementState: Managed`/`Removed`)

### 관리자 리소스
- `OdhDashboardConfig` — UI 기능·리소스 쿼터 제어
- `ConfigMap` — idle 노트북 culling
- `AcceleratorProfile` — GPU 접근 옵션
- `ImageStream`(특정 라벨) — 커스텀 노트북 이미지
- `ServingRuntime`을 감싼 `Template` — 모델 서빙 템플릿

### 엔드유저 리소스
- `Namespace`(`opendatahub.io/dashboard: "true"` 라벨) — 데이터 사이언스 프로젝트
- `Notebook`(Kubeflow API) — 워크벤치 환경
- 특정 어노테이션 `Secret` — "data science connection"
- `DataSciencePipelinesApplication`(DSPA) — 프로젝트별 파이프라인 활성화
- `ServingRuntime` + `InferenceService` — KServe(단일 모델) 또는 ModelMesh(다중 모델) 패턴

## 핵심 패턴

> 처음 GitOps로 기능을 구현할 땐, 대시보드에서 수동으로 리소스를 만든 뒤 생성된 리소스를 추출해 GitOps 레포에 복제하는 방식을 강력 권장.

- **KServe**: `InferenceService`마다 별도 Pod / **ModelMesh**: 여러 모델이 1개 Pod 공유
- `inject-oauth` 어노테이션 — 노트북 OAuth 프록시 자동 구성
- 시크릿은 평문 base64 대신 SealedSecrets/ExternalSecrets 등 외부 도구 필요
- Data Science Pipelines는 네이티브 GitOps 미지원 → Tekton 파이프라인으로 우회
- ArgoCD에 RHOAI 호환 커스텀 health check 필요 (Red Hat AI Services Practice GitHub 참조)

## 워크숍 맥락

[01-ai-on-openshift](01-ai-on-openshift.md)의 GitOps 심화편. RHOAI를 선언적으로 운영할 때 어떤 CR을 어떻게 다루는지 매핑해 줌.
