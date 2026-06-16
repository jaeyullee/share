# 요약 ③ OpenShift AI(RHOAI) 실무

> References 중 **OpenShift AI 플랫폼 실무·GitOps·파이프라인 구축** 자료 3종 요약. 상세는 각 개별 노트 참조.
> 묶음: [[References/01-ai-on-openshift]] · [[References/02-ai-on-openshift-gitops]] · [[References/10-redhat-modular-ai-pipelines]]

## 플랫폼 지식 허브 → 선언적 운영(GitOps) → 파이프라인 모듈화 순으로 실무에 접근한다.

## 1. 지식 허브 — ai-on-openshift.io

- "OpenShift 위 AI/ML·데이터 사이언스의 one-stop shop." RHOAI/ODH 실무의 1차 참고처.
- 주요 섹션: **ODH/RHOAI How-Tos**(GPU·모델 서빙·오토스케일링), **Tools**(Airflow·Spark·MLflow·Kafka·Minio), **Architectural Patterns**, **Predictive/Generative AI 데모**.
- How-to + 베스트 프랙티스 + 동작 코드 + E2E 데모 결합.

## 2. 선언적 운영 — GitOps for OpenShift AI

RHOAI를 **Kubernetes 커스텀 리소스(YAML)**로 GitOps 관리:

- **설치**: `Subscription`(OLM) → `DSCInitialization` → `DataScienceCluster`(컴포넌트 선택).
- **관리자**: `OdhDashboardConfig`, `AcceleratorProfile`(GPU), `ServingRuntime` 템플릿 등.
- **엔드유저**: 대시보드 라벨 `Namespace`, `Notebook`, data science connection `Secret`, `DSPA`(파이프라인), `InferenceService`(서빙).
- **핵심 패턴**: 대시보드로 수동 생성 → 리소스 추출 → GitOps 레포에 복제. KServe(모델당 Pod) vs ModelMesh(Pod 공유). 시크릿은 SealedSecrets/ExternalSecrets 필요. DS Pipelines는 GitOps 미지원 → Tekton 우회.

## 3. 파이프라인 모듈화 — Red Hat 재사용 컴포넌트

- Kubeflow Pipelines를 **재사용 컴포넌트**("코드 없이 꽂아 쓰는 함수")로 모듈화.
- 2계층 레지스트리: Upstream Kubeflow(범용) + Red Hat Data Services(RHOAI 전용). 안정성 태그 alpha/beta/stable.
- 컴포넌트 구조: `component.py`(KFP 데코레이터) + `metadata.yaml` + 테스트. 순차/병렬 조합 후 YAML 컴파일.
- 이점: 표준화·개발시간 단축·plumbing 감소. "작은 데이터셋으로 먼저 테스트."

## 한 줄 정리

**무엇으로 배우고(ai-on-openshift) → 어떻게 운영하고(GitOps CR) → 어떻게 파이프라인을 짜는가(재사용 컴포넌트)**. RHOAI 워크숍 실무의 뼈대. 도구 상세는 [[Tool-Docs/11-openshift-ai]]·[[Tool-Docs/18-kserve]]·[[Tool-Docs/12-kubeflow-pipelines]] 참조.
