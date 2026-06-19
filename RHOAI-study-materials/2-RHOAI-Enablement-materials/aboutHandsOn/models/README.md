# 모델

> 워크벤치(또는 venv)에서 스크립트 실행 → 산출물을 S3/MinIO 버킷 `models/`에 업로드 →
> KServe `storageUri`로 서빙. LLM은 HF 링크(`llm-serving-models.md`).

| 스크립트 | 산출물 | 서빙 런타임 | Day |
|---|---|---|---|
| `train_iris_sklearn.py` | `iris/model.joblib` | MLServer(sklearn) | 1, 6 |
| `train_fraud_sklearn.py` | `fraud/model.joblib` | MLServer(sklearn) | 5, 10, 15 |
| `train_mnist_pytorch.py` | `mnist/1/model.onnx` | OVMS(ONNX) | 2 |
| `train_tf_savedmodel.py` | `tf-fraud/1/` (SavedModel) | KServe tensorflow | 2 |
| `llm-serving-models.md` | (HF 링크) | vLLM(GPU) | 14 |

## S3 업로드 레이아웃 (storageUri 규칙)

```
s3://models/
├── iris/model.joblib          # storageUri: s3://models/iris
├── fraud/model.joblib         # storageUri: s3://models/fraud
├── mnist/1/model.onnx         # storageUri: s3://models/mnist
└── tf-fraud/1/saved_model.pb  # storageUri: s3://models/tf-fraud
```

```bash
mc alias set m http://minio.ai-enablement.svc:9000 minio REPLACE_ME
mc mb m/models
mc cp --recursive mnist/ m/models/mnist/
```

## 실행 환경

- sklearn 스크립트: 워크벤치 기본 이미지(scikit-learn, joblib, pandas).
- `train_mnist_pytorch.py`: `torch`, `torchvision`, `onnx`.
- `train_tf_savedmodel.py`: `tensorflow`, `pandas`, `scikit-learn`.
- 전부 CPU 동작.
