# RHOAI Operator (opendatahub-operator)

> RHOAI 전체를 설치·구성·수명관리하는 **메타(플랫폼) 오퍼레이터**. 자신은 워크로드를 서빙하지 않고, DSCI/DSC CR을 입력으로 받아 하위 컴포넌트와 K8s 리소스를 reconcile한다.
> 영역: [10-플랫폼토대-관계](10-플랫폼토대-관계.md) · 짝: [12-DataScienceCluster-DSCI](12-DataScienceCluster-DSCI.md)

---

## 1. 정의 / 역할
- RHOAI = **오픈소스 조립품**(KServe·KubeRay·Kueue·Kubeflow·llm-d·Feast·MLflow…)을 하나로 묶은 통합 플랫폼. 이 오퍼레이터가 그 "묶는 통합 레이어"다.
- 업스트림 커뮤니티 프로젝트 = **Open Data Hub(ODH)**. RHOAI는 그 상용 지원 배포판(OpenShift가 쿠버네티스에 갖는 관계와 동일).

## 2. 업스트림 / 버전 / 라이프사이클
- 업스트림: **`opendatahub-io/opendatahub-operator`** (Go 모듈 `.../v2`).
- 다운스트림 포크: **`red-hat-data-services/rhods-operator`**, 3.4 브랜치 `rhoai-3.4`.
- 빌드 태그 `//go:build rhoai`로 RHOAI 전용 경로가 ODH 빌드와 분기됨(예: DSCI spec에 ServiceMesh 포함).
- 라이프사이클: **GA** (플랫폼 본체).

## 3. 아키텍처 (상주 vs 잡별)
- **전부 컨트롤 플레인. 상주형 단일 오퍼레이터 파드** (`redhat-ods-operator` 네임스페이스). 잡별 파드 없음.
- **한 매니저 프로세스에 다수 controller-runtime 컨트롤러**를 등록(소스 `internal/controller/`):
  - **DSCInitialization 컨트롤러** — 플랫폼 공통 기반.
  - **DataScienceCluster 컨트롤러** — 컴포넌트 오케스트레이션.
  - **컴포넌트 컨트롤러들** (`components/<name>/`): dashboard, workbenches, kserve, datasciencepipelines, ray, kueue, trainingoperator, **trainer**, modelregistry, trustyai, feastoperator, llamastackoperator, **mlflowoperator**, **sparkoperator**, **modelcontroller**, **modelsasservice**. (컴포넌트마다 전용 컨트롤러 1개)
  - **서비스 컨트롤러들** (`services/`): auth, gateway, monitoring, certconfigmapgenerator, registry, setup.
- 부가 바이너리(같은 레포): `cmd/mcp-server`(플랫폼 헬스/컴포넌트 상태/파드 로그용 MCP 서버), `cmd/health-check`, `cmd/component-codegen`.

## 4. 무엇을 watch 하나
- DSC 컨트롤러는 자신이 만든 **모든 컴포넌트 CR을 `Owns()`**(owner-ref + status watch).
- **DSCI**와 **GatewayConfig**를 `Watches()` (변경 시 DSC 재조정 트리거).

## 5. 컴포넌트 배포 메커니즘 (핵심)
- **기본 = 내장(embedded) 매니페스트**: 오퍼레이터 이미지에 각 컴포넌트의 K8s 매니페스트가 `opt/manifests/`로 번들. DSC가 enable한 컴포넌트의 CR을 만들면, 해당 컴포넌트 컨트롤러가 그 매니페스트를 클러스터에 apply.
- **컴포넌트별 별도 OLM Subscription 없음** — 오퍼레이터가 직접 컴포넌트 컨트롤러 Deployment까지 배포.
- **예외 = MaaS**: enable 시 `AppendOperatorInstallManifests`로 maas-controller 번들(CRD/RBAC/Deployment)을 별도 설치, Tenant reconcile을 maas-controller에 위임.
- `devFlags.manifests`로 컴포넌트 매니페스트를 원격 git에서 덮어쓰기 가능(개발용, 프로덕션 비권장).

## 6. 동작 흐름
1. OLM이 오퍼레이터 파드 설치 → 모든 컨트롤러 등록.
2. DSCI 컨트롤러가 공통 기반(네임스페이스·모니터링·Auth·CA번들·ServiceMesh) 구축.
3. DSC 컨트롤러가 컴포넌트 CR 생성 → 각 컴포넌트 컨트롤러가 실제 리소스 배포(2단계 reconcile).
4. status 집계 → `ComponentsReady`.

## 7. 다른 컴포넌트와의 연동
- **모든 컴포넌트의 상위 관리자.** 이 폴더의 모든 컴포넌트가 이 오퍼레이터에 의해 배포·관리된다.
- DSCI/DSC가 입력, 컴포넌트 CR이 출력.

## 8. 운영 함정
- 별도로 설치한 KubeRay/CodeFlare 등 오퍼레이터가 있으면 충돌 → 컴포넌트 enable 전 제거.
- 언인스톨은 운영자 네임스페이스 ConfigMap에 `DeleteConfigMapLabel=true`를 다는 방식(`setup` 컨트롤러) → 실수로 라벨 달면 플랫폼 제거 시작.

## 9. 출처
- 소스(3.4): https://github.com/red-hat-data-services/rhods-operator/tree/rhoai-3.4
  - 컨트롤러: `/internal/controller/` (datasciencecluster, dscinitialization, components/*, services/*)
- 업스트림: https://github.com/opendatahub-io/opendatahub-operator
- RHOAI 3.4 release notes: docs.redhat.com 3.4 html-single/release_notes/index

## 10. 미확인/주의
- 컴포넌트별 정확 업스트림 점버전은 status `releases[]` 또는 Supported Configs로 확인.
