#!/usr/bin/env python3
"""
Day 5 blue/green test model v2.

Input:
  ../datasets/fraud-credit/fraud_sample.csv

Output:
  fraud-v2/model.joblib
  fraud-v2/sample_request.json

This v2 model intentionally uses a different sklearn estimator from
train_fraud_sklearn.py so Route weight tests can produce visibly different
responses when fraud and fraud-v2 are served behind the same model name.
"""
import json
import os

import joblib
import pandas as pd

CSV = os.path.join(
    os.path.dirname(__file__),
    "../datasets/fraud-credit/fraud_sample.csv",
)
OUTDIR = os.path.join(os.getcwd(), "fraud-v2")
FEATURES = [
    "amount",
    "age",
    "tenure_months",
    "num_claims",
    "credit_score",
    "distance_km",
    "channel",
]


def main():
    from sklearn.dummy import DummyClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    df = pd.read_csv(CSV)
    X, y = df[FEATURES].astype("float32"), df["label"]
    Xtr, Xte, ytr, yte = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # Deliberately predictable v2 for hands-on traffic-split visibility.
    clf = DummyClassifier(strategy="constant", constant=1)
    clf.fit(Xtr, ytr)

    try:
        auc = roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])
        print(f"ROC-AUC = {auc:.3f}")
    except ValueError as exc:
        print(f"ROC-AUC skipped: {exc}")

    os.makedirs(OUTDIR, exist_ok=True)
    joblib.dump(clf, os.path.join(OUTDIR, "model.joblib"))

    req = {
        "inputs": [
            {
                "name": "input-0",
                "shape": [1, len(FEATURES)],
                "datatype": "FP32",
                "data": Xte.iloc[0].tolist(),
            }
        ]
    }
    with open(os.path.join(OUTDIR, "sample_request.json"), "w", encoding="utf-8") as f:
        json.dump(req, f, indent=2)

    print(f"saved -> {OUTDIR}/model.joblib, sample_request.json")


if __name__ == "__main__":
    main()
