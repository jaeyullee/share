# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 실습
## week 1 - Day4




### 모델 준비
```bash
cd /tmp/python3

cat <<'EOF' > models/train_jukebox_onnx.py
import json
import os
import numpy as np
import pandas as pd

FEATURES = ["is_explicit", "duration_ms", "danceability", "energy", "key",
            "loudness", "mode", "speechiness", "acousticness",
            "instrumentalness", "liveness", "valence", "tempo"]
CSV = os.path.join(os.path.dirname(__file__),
                   "../datasets/jukebox-spotify/songs_sample.csv")
OUTDIR = os.path.join(os.path.dirname(__file__), "jukebox")


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
EOF

cat <<'EOF' > models/train_mnist_pytorch.py
import json
import os

OUTDIR = os.path.join(os.path.dirname(__file__), "mnist")


def main():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 16, 3, 1)
            self.conv2 = nn.Conv2d(16, 32, 3, 1)
            self.fc1 = nn.Linear(32 * 12 * 12, 64)
            self.fc2 = nn.Linear(64, 10)

        def forward(self, x):
            x = F.relu(self.conv1(x))
            x = F.relu(self.conv2(x))
            x = F.max_pool2d(x, 2)
            x = torch.flatten(x, 1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    tfm = transforms.Compose([transforms.ToTensor(),
                              transforms.Normalize((0.1307,), (0.3081,))])
    root = os.path.join(os.path.dirname(__file__), "../datasets/_mnist_cache")
    train = datasets.MNIST(root, train=True, download=True, transform=tfm)
    loader = DataLoader(train, batch_size=64, shuffle=True)

    model = Net()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    model.train()
    for epoch in range(1):  # CPU: 1 epoch ~ 충분히 동작 확인
        for i, (x, y) in enumerate(loader):
            opt.zero_grad()
            loss = F.cross_entropy(model(x), y)
            loss.backward()
            opt.step()
            if i % 200 == 0:
                print(f"epoch{epoch} step{i} loss={loss.item():.3f}")

    os.makedirs(os.path.join(OUTDIR, "1"), exist_ok=True)
    torch.save(model.state_dict(), os.path.join(OUTDIR, "model.pt"))

    model.eval()
    dummy = torch.randn(1, 1, 28, 28)
    torch.onnx.export(model, dummy, os.path.join(OUTDIR, "1", "model.onnx"),
                      input_names=["input"], output_names=["output"],
                      dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
                      opset_version=17)

    req = {"inputs": [{"name": "input", "shape": [1, 1, 28, 28],
                       "datatype": "FP32", "data": dummy.flatten().tolist()}]}
    json.dump(req, open(os.path.join(OUTDIR, "sample_request.json"), "w"))
    print(f"saved -> {OUTDIR}/model.pt, 1/model.onnx, sample_request.json")


if __name__ == "__main__":
    main()
EOF

cat <<'EOF' > models/train_tf_savedmodel.py
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
EOF

python3 -m venv .venv
source .venv/bin/activate

## tensorflow 사용하는 python빌드는 vm 설정에 따라 지원여부 확인이 필요
pip install tensorflow numpy pandas
python3 models/train_jukebox_onnx.py
ls /

mc alias set truenas http://192.168.20.5:9000 <minio_id> <minio_pw>
mc mb --ignore-existing truenas/rhoai-models
mc cp  truenas/rhoai-models/
mc ls truenas/rhoai-models/
```