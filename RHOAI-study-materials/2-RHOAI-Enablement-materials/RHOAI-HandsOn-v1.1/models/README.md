# 모델

> 학습/변환 스크립트는 **RHOAI 워크벤치(또는 venv)**에서 실행해 산출물을 만든 뒤,
> S3/MinIO 버킷(예: `rhoai-models`)에 업로드 → KServe `storageUri`로 서빙한다.
> LLM은 직접 학습하지 않고 **HF 링크**로 받는다(`llm-serving-models.md`).

| 스크립트 | 산출물 | 서빙 런타임 | Day |
|---|---|---|---|
| `train_iris_sklearn.py` | `iris/model.joblib` | MLServer(sklearn) | 3, 6 |
| `train_fraud_sklearn.py` | `fraud/model.joblib` | MLServer(sklearn) | 5 |
| `train_jukebox_onnx.py` | `jukebox/1/model.onnx` (+labels) | OVMS(ONNX) | 4, 8 (AI500 재현) |
| `train_mnist_pytorch.py` | `mnist/1/model.onnx` | OVMS(ONNX) | 4 |
| `train_tf_savedmodel.py` | `tf-fraud/1/` (SavedModel) | KServe tensorflow | 4 |
| `llm-serving-models.md` | (HF 링크) | vLLM(GPU) | 14 |

## 실행 위치와 산출물 경로

학습 스크립트는 `models/` 디렉터리 아래가 아니라, 실행한 현재 디렉터리(`pwd`) 아래에 산출물을 만든다.

```bash
cd /tmp/python3
python3 models/train_jukebox_onnx.py
# /tmp/python3/jukebox/1/model.onnx 생성
```

## S3 업로드 레이아웃 (storageUri 규칙)

OVMS/TF는 `<model>/<version>/...` 디렉토리 레이아웃을, `storageUri`는 **상위 폴더**를 가리킨다.

```
s3://rhoai-models/
├── iris/model.joblib                 # storageUri: s3://rhoai-models/iris
├── fraud/model.joblib                # storageUri: s3://rhoai-models/fraud
├── fraud-kfp/v1-<KFP_RUN_ID>/model.joblib  # Day 7 artifact -> Day 8 v1
├── fraud-kfp/v2-<KFP_RUN_ID>/model.joblib  # Day 7 artifact -> Day 8 v2
├── jukebox/1/model.onnx              # storageUri: s3://rhoai-models/jukebox
├── mnist/1/model.onnx                # storageUri: s3://rhoai-models/mnist
└── tf-fraud/1/saved_model.pb         # storageUri: s3://rhoai-models/tf-fraud
```

업로드 예(mc):
```bash
mc alias set m http://minio.jukebox.svc:9000 <MINIO_ID> <MINIO_PW>
mc mb m/rhoai-models
mc cp --recursive jukebox/ m/rhoai-models/jukebox/
```

## 실행 환경

- sklearn 스크립트: 워크벤치 기본 이미지로 충분(scikit-learn, joblib, pandas).
- `train_jukebox_onnx.py`: `tensorflow`, `tf2onnx`, `onnx` 필요(스크립트 상단 주석).
- `train_mnist_pytorch.py`: `torch`, `torchvision`, `onnx`.
- 전부 **CPU 동작**(jukebox/mnist는 학습도 CPU로 수 분 내).
