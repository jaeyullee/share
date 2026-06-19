#!/usr/bin/env python3
"""
Day 6(Jupyter Workbench RandomForest 훈련)용 iris CSV.

curriculum v1.0 Day 6 = "iris로 RandomForest 훈련(.pkl)". sklearn 내장이라
워크벤치 안에서 load_iris()로 바로 쓸 수 있으나, 폐쇄망/재현성 목적으로 CSV도 둔다.

사용: python export_iris.py   ->  iris.csv (150 rows)
"""
from sklearn.datasets import load_iris
import pandas as pd

ds = load_iris(as_frame=True)
df = ds.frame.copy()
df["species"] = df["target"].map(dict(enumerate(ds.target_names)))
df.to_csv("iris.csv", index=False)
print(f"wrote {len(df)} rows -> iris.csv")
print(df.head())
