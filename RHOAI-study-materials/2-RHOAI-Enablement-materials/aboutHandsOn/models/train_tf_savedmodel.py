#!/usr/bin/env python3
"""
Day 2(TensorFlow 모델 배포) — TensorFlow SavedModel.

curriculum v0.9 Day 2: "TensorFlow SavedModel 배포(modelFormat: tensorflow)".
간단한 분류기를 학습해 TF SavedModel 포맷으로 저장한다(KServe tensorflow 런타임용).
여기서는 fraud_sample.csv(이진분류)를 재사용해 TF로도 학습 경로를 보여준다.

입력:  ../datasets/fraud-credit/fraud_sample.csv
출력:  tf-fraud/1/  (SavedModel 디렉토리; KServe storageUri는 상위 tf-fraud/ 지정)
       tf-fraud/sample_request.json
패키지: tensorflow, pandas, scikit-learn
"""
import json
import os
import pandas as pd

CSV = os.path.join(os.path.dirname(__file__),
                   "../datasets/fraud-credit/fraud_sample.csv")
OUTDIR = os.path.join(os.path.dirname(__file__), "tf-fraud")
FEATURES = ["amount", "age", "tenure_months", "num_claims",
            "credit_score", "distance_km", "channel"]


def main():
    import tensorflow as tf
    from tensorflow import keras
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split

    df = pd.read_csv(CSV)
    X = StandardScaler().fit_transform(df[FEATURES].astype("float32"))
    y = df["label"].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)

    model = keras.Sequential([
        keras.layers.Input(shape=(len(FEATURES),), name="input"),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dense(1, activation="sigmoid", name="output"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    model.fit(Xtr, ytr, validation_data=(Xte, yte), epochs=10, batch_size=64, verbose=2)

    os.makedirs(OUTDIR, exist_ok=True)
    # KServe tensorflow 런타임은 <model>/<version>/saved_model.pb 레이아웃을 기대
    model.export(os.path.join(OUTDIR, "1"))  # TF SavedModel

    req = {"inputs": [{"name": "input", "shape": [1, len(FEATURES)],
                       "datatype": "FP32", "data": Xte[0].tolist()}]}
    json.dump(req, open(os.path.join(OUTDIR, "sample_request.json"), "w"), indent=2)
    print(f"saved SavedModel -> {OUTDIR}/1/ , sample_request.json")


if __name__ == "__main__":
    main()
