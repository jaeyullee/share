# OpenVINO — 공식 문서

- **링크**: https://docs.openvino.ai/2025/index.html
- **분류**: Tool-Docs / AI
- **한 줄**: Intel 하드웨어(CPU·GPU·NPU)에서 모델을 최적화·가속 추론하는 Intel의 오픈소스 툴킷.

## 핵심 목적

① 신경망 모델 최적화(크기·연산량 축소) ② Intel 프로세서에서 추론 가속. 전통 AI와 생성 AI 워크플로 모두 지원.

## 워크플로 (3단계)

1. **Convert** — PyTorch/TensorFlow/ONNX/JAX/Keras/PaddlePaddle 모델을 OpenVINO IR(intermediate representation)로 변환
2. **Optimize** — 양자화·프루닝·가중치 압축으로 복잡도 축소(정확도 유지)
3. **Deploy** — 로컬·서버·OpenVINO Model Server(Docker/K8s)로 추론

## 문서 범위

플랫폼별 설치, 인터랙티브 Python 노트북, 샘플 앱, 수백 개 연산 API 레퍼런스, LLM 최적화, 엣지·클라우드 배포 전략.

## 워크숍 맥락

[18-kserve](18-kserve.md)의 ServingRuntime 백엔드 중 하나(OpenVINO Model Server). GPU 없이 Intel CPU에서 효율 추론할 때의 최적화 경로.
