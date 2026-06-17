# Model Catalog

> register/deploy 이전 단계에서 GenAI 모델을 **발견·평가**하는 큐레이트 라이브러리. model-registry 컴포넌트의 일부.
> 영역: [50-모델거버넌스-관계](50-모델거버넌스-관계.md)

---

## 1. 정의 / 역할
- 모델 카드에 아키텍처/라이선스/검증 버전/벤치마크(OpenLLM, TTFT, TPS)/인증 HW 표시.
- 분류 3종: **Red Hat AI models**(직접 지원), **Red Hat AI validated models**(RH 벤치마크 서드파티), **Other models**(관리자 커스텀).

## 2. 라이프사이클
- 2.21 TP → 2.25 GA(Model Registry 동반) → **3.4 GA**. 3.4 신규: **IBM Power·Z 멀티아키텍처**.

## 3. 아키텍처
- **대시보드 UI + 백엔드 catalog 서버** 조합. **model-registry 컴포넌트의 일부**(별도 DSC 컴포넌트 아님). catalog 서버 **Deployment + Service** 배포. `rhoai-model-registries` 네임스페이스.

## 4. 동작 / 소스 / 메타데이터
- 소스 = **`sources.yaml`** → **`model-catalog-sources` ConfigMap**으로 Pod에 마운트.
- 소스 필드: `name`/`id`/`type`/`properties`/`enabled`(기본 true). 지원 type = **`yaml`**(`properties.yamlCatalogPath`).
- 모델 패키징: **OCI ModelCar** 이미지, registry.redhat.io 호스팅.
- **Hugging Face**: 샘플 카탈로그에 HF 항목 존재하나, "동적 HF 검색 소스"는 문서·코드 상충 → 미확인. `model-metadata-collection`이 HF에서 메타데이터 추출해 **정적 YAML 카탈로그 생성**하는 게 실체에 가까움(추정).

## 5. allow/disallow
- 관리자가 `rhoai-model-registries`의 **`model-catalog-sources` ConfigMap** 편집. 소스 단위 `enabled: true/false`. 모델 제외는 `yaml` 소스의 **`excludedModels`**(`model-a:1.0` 또는 패턴 `model-b:*`).

## 6. 배포 위저드 연동
- AI hub → Models → Catalog → [모델] → Deploy. 모델 타입(Generative/Predictive) → 리소스 → serving runtime. 3.4: 일부 모델에 **권장 vLLM 런타임 템플릿** + tool-calling 메타데이터. 카탈로그에서 직접 registry로 register도 가능. → [51-Model-Registry](51-Model-Registry.md)

## 7. 운영 함정
- 3.4-EA1: ppc64le 배포가 registry deployments 탭 미표시(known issue).
- 커스텀 소스는 GitOps 아닌 **ConfigMap 수동 편집**(형상관리 주의).
- HF "동적 소스"는 미확정. disconnected 지원 여부 미확인.

## 8. 출처
- 설정: `opendatahub-io/model-registry .../kustomize/options/catalog/README.md`
- RHOAI 3.4 working_with_the_model_catalog
