#!/usr/bin/env python3
"""
Day 7 — KFP v2 3단계 파이프라인 (전처리 → 훈련 → 평가).
AI500 jukebox(3-prod_datascience)의 축소판. fraud_sample.csv로 이진분류 학습.

컴파일:
  pip install kfp==2.* kfp-kubernetes
  python day07-pipeline.py            # -> jukebox_pipeline.yaml 생성
업로드/실행: 대시보드 Pipelines에 jukebox_pipeline.yaml 업로드 → Run 생성.
재사용: epochs/n_estimators 등 파라미터 바꿔 재실행 → Run 비교.
"""
from kfp import dsl, compiler


@dsl.component(base_image="python:3.11",
               packages_to_install=["pandas==2.2.3", "scikit-learn==1.6.1"])
def preprocess(in_csv_url: str, train_out: dsl.Output[dsl.Dataset],
               test_out: dsl.Output[dsl.Dataset]):
    import pandas as pd
    from sklearn.model_selection import train_test_split
    df = pd.read_csv(in_csv_url).dropna()
    tr, te = train_test_split(df, test_size=0.2, random_state=42)
    tr.to_csv(train_out.path, index=False)
    te.to_csv(test_out.path, index=False)
    print(f"train={len(tr)} test={len(te)}")


@dsl.component(base_image="python:3.11",
               packages_to_install=["pandas==2.2.3", "scikit-learn==1.6.1", "joblib"])
def train(train_in: dsl.Input[dsl.Dataset], n_estimators: int,
          model_out: dsl.Output[dsl.Model]):
    import pandas as pd, joblib
    from sklearn.ensemble import RandomForestClassifier
    feats = ["amount", "age", "tenure_months", "num_claims",
             "credit_score", "distance_km", "channel"]
    df = pd.read_csv(train_in.path)
    clf = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    clf.fit(df[feats], df["label"])
    joblib.dump(clf, model_out.path)


@dsl.component(base_image="python:3.11",
               packages_to_install=["pandas==2.2.3", "scikit-learn==1.6.1", "joblib"])
def evaluate(test_in: dsl.Input[dsl.Dataset], model_in: dsl.Input[dsl.Model],
             metrics: dsl.Output[dsl.Metrics]):
    import pandas as pd, joblib
    from sklearn.metrics import roc_auc_score, accuracy_score
    feats = ["amount", "age", "tenure_months", "num_claims",
             "credit_score", "distance_km", "channel"]
    df = pd.read_csv(test_in.path)
    clf = joblib.load(model_in.path)
    proba = clf.predict_proba(df[feats])[:, 1]
    auc = roc_auc_score(df["label"], proba)
    acc = accuracy_score(df["label"], clf.predict(df[feats]))
    metrics.log_metric("roc_auc", float(auc))
    metrics.log_metric("accuracy", float(acc))
    print(f"AUC={auc:.3f} ACC={acc:.3f}")


@dsl.pipeline(name="jukebox-fraud-pipeline",
              description="preprocess -> train -> evaluate (AI500 축소판)")
def pipe(in_csv_url: str = "https://raw.githubusercontent.com/REPLACE/fraud_sample.csv",
         n_estimators: int = 100):
    p = preprocess(in_csv_url=in_csv_url)
    t = train(train_in=p.outputs["train_out"], n_estimators=n_estimators)
    evaluate(test_in=p.outputs["test_out"], model_in=t.outputs["model_out"])


if __name__ == "__main__":
    compiler.Compiler().compile(pipe, "jukebox_pipeline.yaml")
    print("compiled -> jukebox_pipeline.yaml")
