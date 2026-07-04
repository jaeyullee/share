#!/usr/bin/env python3
"""
AI500 jukebox 재현(미니) — Spotify 13 피처 -> country 다중분류 Keras 모델 -> ONNX export.

원본 jukebox(3-prod_datascience/train_model.py)는 country별 멀티헤드 입력 Dense NN을
TensorFlow로 학습 후 tf2onnx로 ONNX 변환 -> KServe(OpenVINO Model Server)로 서빙한다.
이 스크립트는 그 경로를 SNO(CPU) 워크벤치에서 빠르게 재현하기 위한 단순화 버전이다.

입력:  ../datasets/jukebox-spotify/songs_sample.csv
출력:
  jukebox/1/model.onnx        # OVMS/KServe 디렉토리 레이아웃(<name>/<version>/model.onnx)
  jukebox/labels.json         # country 라벨 인덱스
  jukebox/sample_request.json # KServe v2 추론 요청 예시

필요 패키지(워크벤치): tensorflow, tf2onnx, onnx, scikit-learn, pandas, numpy
  pip install "tensorflow==2.*" tf2onnx onnx scikit-learn pandas "numpy<2"

서빙(요약): OVMS ServingRuntime + InferenceService(storageUri: s3://.../jukebox)
  manifests/day08-model-registry/ 및 day03-serving 의 ONNX 예시 참조.
"""
import json
import os
import numpy as np
import pandas as pd

FEATURES = ["is_explicit", "duration_ms", "danceability", "energy", "key",
            "loudness", "mode", "speechiness", "acousticness",
            "instrumentalness", "liveness", "valence", "tempo"]
CSV = os.path.join(os.path.dirname(__file__),
                   "../datasets/jukebox-spotify/songs_sample.csv")
OUTDIR = os.path.join(os.getcwd(), "jukebox")


def main():
    from sklearn.preprocessing import MinMaxScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    import tensorflow as tf
    from tensorflow import keras

    df = pd.read_csv(CSV).dropna()
    X = df[FEATURES].astype("float32")
    le = LabelEncoder()
    y = le.fit_transform(df["country"])
    y_oh = keras.utils.to_categorical(y)

    scaler = MinMaxScaler()
    Xs = scaler.fit_transform(X).astype("float32")
    Xtr, Xte, ytr, yte = train_test_split(Xs, y_oh, test_size=0.2, random_state=42)

    model = keras.Sequential([
        keras.layers.Input(shape=(len(FEATURES),), name="input"),
        keras.layers.Dense(64, activation="relu"),
        keras.layers.Dense(128, activation="relu"),
        keras.layers.Dense(y_oh.shape[1], activation="softmax", name="output"),
    ])
    model.compile(optimizer="adam", loss="categorical_crossentropy",
                  metrics=["accuracy"])
    model.fit(Xtr, ytr, validation_data=(Xte, yte), epochs=15, batch_size=32, verbose=2)
    acc = model.evaluate(Xte, yte, verbose=0)[1]
    print(f"test accuracy = {acc:.3f}")

    os.makedirs(os.path.join(OUTDIR, "1"), exist_ok=True)

    # Keras -> ONNX
    import tf2onnx, onnx
    spec = (tf.TensorSpec((None, len(FEATURES)), tf.float32, name="input"),)
    onnx_model, _ = tf2onnx.convert.from_keras(model, input_signature=spec, opset=17)
    onnx.save(onnx_model, os.path.join(OUTDIR, "1", "model.onnx"))

    json.dump({i: c for i, c in enumerate(le.classes_.tolist())},
              open(os.path.join(OUTDIR, "labels.json"), "w"),
              ensure_ascii=False, indent=2)

    # KServe v2(OVMS) 추론 요청 예시 — 첫 테스트 샘플
    sample = Xte[0].tolist()
    req = {"inputs": [{"name": "input", "shape": [1, len(FEATURES)],
                       "datatype": "FP32", "data": sample}]}
    json.dump(req, open(os.path.join(OUTDIR, "sample_request.json"), "w"), indent=2)
    print(f"saved -> {OUTDIR}/1/model.onnx, labels.json, sample_request.json")


if __name__ == "__main__":
    main()
