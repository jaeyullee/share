# Red Hat — Build modular AI pipelines with OpenShift AI and reusable components

- **링크**: https://developers.redhat.com/articles/2026/06/03/build-modular-ai-pipelines-openshift-ai-and-reusable-components
- **분류**: References (블로그)
- **한 줄**: OpenShift AI의 Kubeflow Pipelines를 재사용 가능 컴포넌트로 모듈화해 AI 파이프라인을 구축하는 방법.

## 재사용 컴포넌트란

"코드를 처음부터 짜지 않고 AI 워크플로에 꽂아 쓰는 함수." 데이터 전처리·학습·평가·최적화·배포 등 특정 작업을 담당. 공유 카탈로그의 검증된 구현을 재사용.

## 컴포넌트 레지스트리 (2계층)

1. **Upstream Kubeflow 레포** — 여러 플랫폼/환경 공용 범용 컴포넌트
2. **Red Hat Data Services 레포** — 내부 의존성·OpenShift AI 전용 기능 컴포넌트

안정성 태그: **alpha**(실험) / **beta**(개선) / **stable**(프로덕션).

## 모듈형 파이프라인 구축

표준 디렉토리 구조 — `component.py`(KFP 데코레이터 로직), `metadata.yaml`, `__init__.py`, `OWNERS`, 테스트·문서. 컴포넌트를 순차/병렬로 조합(예: `component_one` 출력 → `component_two` 입력), Python 정의를 YAML로 컴파일해 OpenShift AI에서 실행.

## 이점

- 표준화, 개발 시간 단축, 협업 향상, 리소스 효율("plumbing에 덜 쓰고 모델 성능에 더 집중"), 유지보수 부담 감소
- GenAI: 데이터 정제·포맷 변환·학습 오케스트레이션·체크포인트·평가 로직 중복 제거

## 실전 팁

- 단일 컴포넌트 파이프라인으로 시작 → 다중·병렬로 확장
- 스캐폴딩: `make component CATEGORY=data_processing NAME=my_preprocessor`
- 입력 검증으로 장시간 실패 예방, 명확한 파라미터 네이밍, 다양한 입력 타입(아티팩트/S3 URL/파일 경로) 지원
- "항상 작은 데이터셋으로 먼저 테스트"

## 워크숍 맥락

[../Tool-Docs/12-kubeflow-pipelines](../Tool-Docs/12-kubeflow-pipelines.md)·[../Tool-Docs/13-kfp-sdk](../Tool-Docs/13-kfp-sdk.md)의 실전 적용. RHOAI MLOps 파이프라인을 재사용 컴포넌트로 설계할 때 핵심 참고.
