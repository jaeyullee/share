#!/usr/bin/env python3
"""
Day 5(고객 모델 온보딩) / Day 10(신용평가 E2E) / Day 15(사기탐지) 용 sklearn 이진분류 모델.

입력:  ../datasets/fraud-credit/fraud_sample.csv
출력:
  fraud/model.joblib
  fraud/sample_request.json   # KServe v2(MLServer) 요청 예시(7 피처)

서빙: day01-kserve-serving(동일 sklearn ServingRuntime), Day3 카나리/Blue-Green으로 확장.
패키지: scikit-learn, pandas, joblib
"""
import json
import os
import joblib
import pandas as pd

CSV = os.path.join(os.path.dirname(__file__),
                   "../datasets/fraud-credit/fraud_sample.csv")
OUTDIR = os.path.join(os.path.dirname(__file__), "fraud")
FEATURES = ["amount", "age", "tenure_months", "num_claims",
            "credit_score", "distance_km", "channel"]


def main():
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score

    df = pd.read_csv(CSV)
    X, y = df[FEATURES].astype("float32"), df["label"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = GradientBoostingClassifier(random_state=42)
    clf.fit(Xtr, ytr)
    auc = roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])
    print(f"ROC-AUC = {auc:.3f}")

    os.makedirs(OUTDIR, exist_ok=True)
    joblib.dump(clf, os.path.join(OUTDIR, "model.joblib"))

    req = {"inputs": [{"name": "input-0", "shape": [1, len(FEATURES)],
                       "datatype": "FP32", "data": Xte.iloc[0].tolist()}]}
    json.dump(req, open(os.path.join(OUTDIR, "sample_request.json"), "w"), indent=2)
    print(f"saved -> {OUTDIR}/model.joblib, sample_request.json")


if __name__ == "__main__":
    main()
