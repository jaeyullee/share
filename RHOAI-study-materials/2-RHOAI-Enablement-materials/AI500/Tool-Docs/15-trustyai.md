# TrustyAI — 공식 GitHub Org

- **링크**: https://github.com/trustyai-explainability
- **분류**: Tool-Docs / AI
- **한 줄**: 설명가능성·공정성·drift·LLM 평가/가드레일을 제공하는 Red Hat·IBM의 책임 있는 AI 툴킷.

## 무엇인가

"로컬·글로벌 모델 설명, 공정성 지표, drift 지표, 텍스트 detoxification, LLM 벤치마킹, LLM 가드레일" 등 책임 있는 AI 워크플로 도구. 투명·공정·설명가능한 ML 시스템 구축 지원.

## 주요 프로젝트

1. **TrustyAI Explainability** — XAI 알고리즘·drift·공정성 측정 Java 라이브러리
2. **TrustyAI Service** — 코어 라이브러리를 노출하는 컨테이너 REST 서버 (KServe·모델 서버 연동)
3. **TrustyAI Operator** — K8s 컨트롤러 (ODH·RHOAI 기본 포함)
4. **Python Library** — Jupyter 친화 바인딩
5. **LM Evaluation & Guardrails** — LLM 벤치마킹·유해 출력 방어

## 핵심 역량

편향 모니터링, 모델 drift 탐지, 성능 벤치마킹, 설명 생성(SHAP/LIME 계열). 프로덕션 AI의 공정성·해석가능성 감사.

## 워크숍 맥락

RHOAI의 모델 모니터링·신뢰성 레이어. [[11-openshift-ai]]에 기본 통합. 용어집의 Bias Detection·SHAP·Counterfactuals와 직결.
