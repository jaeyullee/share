# KServe — 공식 문서

- **링크**: https://kserve.github.io/website/master/modelserving/control_plane/ (문서 홈: https://kserve.github.io/website/)
- **분류**: Tool-Docs / AI
- **한 줄**: Kubernetes 위에서 예측·생성 AI 모델을 표준화된 방식으로 서빙하는 분산 추론 플랫폼 (CNCF incubating).

## 무엇인가

"a standardized distributed generative and predictive AI inference platform for scalable, multi-framework deployment on Kubernetes." 생성·예측 모델을 통합 플랫폼에서 배포.

## 주요 기능

**Generative AI**
- vLLM·llm-d 최적화 백엔드
- OpenAI 호환 추론 프로토콜
- GPU 가속·메모리 관리, 모델 캐싱·KV cache 오프로딩
- Hugging Face 네이티브 통합

**Predictive AI**
- 멀티 프레임워크(TensorFlow, PyTorch, scikit-learn, XGBoost, ONNX)
- 요청 기반 오토스케일링 + **scale-to-zero**
- **Canary 롤아웃**·추론 파이프라인
- 내장 설명가능성·모니터링

## 아키텍처

- **InferenceService API** — 모델 배포 기본 인터페이스
- **Control Plane** — K8s 리소스·배포 관리
- **Data Plane** — 실제 추론 요청 처리
- **ModelMesh**(옵션) — 고밀도 다중 모델 서빙
- **Knative 통합** — 서버리스 배포·오토스케일·canary

## 워크숍 맥락

RHOAI 모델 서빙의 단일 모델 경로. [11-openshift-ai](11-openshift-ai.md)에서 `InferenceService`+`ServingRuntime`으로 배포. [../References/02-ai-on-openshift-gitops](../References/02-ai-on-openshift-gitops.md) 참고. (control_plane 하위 페이지는 404 — README 기반 정리)
