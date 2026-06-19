#!/usr/bin/env python3
"""
Day 1(KServe 기본 배포) / Day 6(Workbench RandomForest) 용 sklearn 모델.

curriculum v0.9:
  - Day 1: "사전훈련 scikit-learn 모델 준비" -> ServingRuntime + InferenceService
  - Day 6: "iris로 RandomForest 훈련(.pkl 저장), 정확도 90%+"

출력:
  iris/model.joblib   # MLServer(sklearn ServingRuntime)가 기대하는 산출물
  iris/sample_request.json  # KServe v2 추론 요청 예시(4 피처)

서빙: manifests/day01-kserve-serving.yaml 참조 (sklearn ServingRuntime + ISVC).
패키지: scikit-learn, joblib  (워크벤치 기본 이미지에 포함)
"""
import json
import os
import joblib

OUTDIR = os.path.join(os.path.dirname(__file__), "iris")


def main():
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    X, y = load_iris(return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(Xtr, ytr)
    acc = accuracy_score(yte, clf.predict(Xte))
    print(f"accuracy = {acc:.3f}")

    os.makedirs(OUTDIR, exist_ok=True)
    joblib.dump(clf, os.path.join(OUTDIR, "model.joblib"))

    # MLServer v2 inference protocol 요청 예시
    req = {"inputs": [{"name": "input-0", "shape": [1, 4], "datatype": "FP32",
                       "data": Xte[0].tolist()}]}
    json.dump(req, open(os.path.join(OUTDIR, "sample_request.json"), "w"), indent=2)
    print(f"saved -> {OUTDIR}/model.joblib, sample_request.json")


if __name__ == "__main__":
    main()
