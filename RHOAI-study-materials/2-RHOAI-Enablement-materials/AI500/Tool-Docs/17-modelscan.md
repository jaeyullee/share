# ModelScan — 공식 GitHub

- **링크**: https://github.com/protectai/modelscan
- **분류**: Tool-Docs / AI
- **한 줄**: 머신러닝 모델 파일에 숨겨진 악성 코드를 로드 전에 탐지하는 보안 스캐너 (Protect AI).

## 해결하는 문제

**모델 직렬화 공격(serialization attack)** — 저장된 모델 파일에 악성 코드를 주입. PyTorch 등은 모델 로드 시 내장 코드를 자동 실행하므로, 악성 모델은 즉시 시스템을 침해한다("the second you load the model the exploit has executed"). 자격증명 탈취·데이터 탈취/오염·모델 조작 위험.

## 스캔 지원 포맷

- **Pickle** (PyTorch, Sklearn, XGBoost)
- **H5/HDF5** (Keras)
- **SavedModel** (TensorFlow)
- **Keras V3**
- Cloudpickle, Dill, Joblib

## 동작 방식

모델을 위험하게 로드하지 않고 **바이트 단위로 raw 데이터를 읽어** 안전하지 않은 코드 시그니처를 탐색. 빠르고(보통 수 초) 안전. 심각도 CRITICAL/HIGH/MEDIUM/LOW 분류.

## 사용법

```
pip install modelscan
modelscan -p /path/to/model_file.pkl
```
CLI·Python 통합·커스텀 리포트(console/JSON) 지원.

## 워크숍 맥락

AI 보안 축. 외부에서 받은 모델(예: Hugging Face)을 RHOAI에 서빙하기 전 검증하는 supply chain 보안 게이트. [[04-AI-보안-관찰성-기초]]와 연계.
