# AI500 — RHOAI MLOps Workshop 참고자료 정리

> 출처: [rhoai-mlops lab-instructions — The Reference Track](https://rhoai-mlops.github.io/lab-instructions/#/9-the-reference-track/references)
> 워크숍 Reference Track의 링크들을 직접 타고 들어가 각 자료를 개별 노트로 정리한 모음. 정리 작성일: 2026-06-12.

워크숍 용어 정의는 [[용어집-Glossary]] 참고.

---

## 주제별 요약 (References 10개 → 3개)

빠르게 훑을 땐 아래 3개 요약부터. 상세는 각 개별 노트로.

| # | 요약 | 묶은 자료 |
|---|---|---|
| ① | [[요약-01-ML-신경망-기초]] | 03 W3Schools · 04 3Blue1Brown · 05 TF Playground · 09 CNN Explainer |
| ② | [[요약-02-MLOps-방법론-실전]] | 06 Made With ML · 07 Google MLOps · 08 Cookiecutter |
| ③ | [[요약-03-OpenShift-AI-실무]] | 01 ai-on-openshift · 02 GitOps · 10 모듈형 파이프라인 |
| ④ | [[요약-04-도구-한눈에]] | Tool-Docs 20개 전체 (AI 10 + DevOps 10) |

---

## References — 학습 자료 (10)

| # | 자료 | 한 줄 |
|---|---|---|
| 01 | [[References/01-ai-on-openshift]] | OpenShift 위 AI/ML 운영 종합 지식 허브 |
| 02 | [[References/02-ai-on-openshift-gitops]] | RHOAI를 K8s CR로 GitOps 관리하는 법 |
| 03 | [[References/03-w3schools-data-science]] | Python 데이터 사이언스 입문 튜토리얼 |
| 04 | [[References/04-3blue1brown-neural-networks]] | 신경망 기초 시각화 영상 시리즈 |
| 05 | [[References/05-tensorflow-playground]] | 신경망 인터랙티브 실험 도구 |
| 06 | [[References/06-made-with-ml]] | 프로덕션 ML 실전 커리큘럼 |
| 07 | [[References/07-google-mlops]] | MLOps 성숙도 3단계 정의 |
| 08 | [[References/08-cookiecutter-data-science]] | DS 프로젝트 표준 구조 템플릿 |
| 09 | [[References/09-cnn-explainer]] | CNN 동작 인터랙티브 시각화 |
| 10 | [[References/10-redhat-modular-ai-pipelines]] | 재사용 컴포넌트로 모듈형 AI 파이프라인 |

## Tool-Docs / AI 도구 (10)

| # | 도구 | 한 줄 |
|---|---|---|
| 11 | [[Tool-Docs/11-openshift-ai]] | RHOAI 통합 MLOps 플랫폼 (워크숍 본체) |
| 12 | [[Tool-Docs/12-kubeflow-pipelines]] | K8s ML 워크플로 오케스트레이션 |
| 13 | [[Tool-Docs/13-kfp-sdk]] | Python으로 파이프라인 작성 SDK |
| 14 | [[Tool-Docs/14-kfp-kubernetes]] | KFP에 K8s 기능 추가 애드온 |
| 15 | [[Tool-Docs/15-trustyai]] | 설명가능성·공정성·drift 책임 AI |
| 16 | [[Tool-Docs/16-dvc]] | 데이터·모델 버전 관리 |
| 17 | [[Tool-Docs/17-modelscan]] | 모델 직렬화 공격 탐지 보안 스캐너 |
| 18 | [[Tool-Docs/18-kserve]] | K8s 분산 추론/모델 서빙 플랫폼 |
| 19 | [[Tool-Docs/19-openvino]] | Intel HW 모델 최적화·추론 가속 |
| 20 | [[Tool-Docs/20-feast]] | Feature Store |

## Tool-Docs / GitOps·DevOps 도구 (10)

| # | 도구 | 한 줄 |
|---|---|---|
| 21 | [[Tool-Docs/21-argocd]] | 선언적 GitOps CD |
| 22 | [[Tool-Docs/22-tekton]] | K8s 네이티브 CI/CD 프레임워크 |
| 23 | [[Tool-Docs/23-pytest]] | Python 테스트 프레임워크 |
| 24 | [[Tool-Docs/24-black]] | Python 코드 포매터 |
| 25 | [[Tool-Docs/25-flake8]] | Python 린터 |
| 26 | [[Tool-Docs/26-kubelinter]] | K8s YAML/Helm 정적 분석 |
| 27 | [[Tool-Docs/27-helm-lint]] | Helm 차트 검증 |
| 28 | [[Tool-Docs/28-sonarqube]] | 코드 품질·보안 게이트 |
| 29 | [[Tool-Docs/29-gitea]] | 셀프호스팅 Git 서비스 |
| 30 | [[Tool-Docs/30-grafana]] | 관찰성·시각화 플랫폼 |

---

## 비고

- 04(YouTube), 05·09(JS 인터랙티브 사이트)는 본문 fetch 불가 → 각각 검색·GitHub README·논문 기반으로 정리.
- 11(OpenShift AI), 28(SonarQube) 공식 문서는 봇 차단(403/404) → 확립된 사실 기반으로 정리(해당 노트에 명시).
- 12·18 등 일부 페이지는 하위 경로가 404여서 상위/README로 대체(노트에 명시).
