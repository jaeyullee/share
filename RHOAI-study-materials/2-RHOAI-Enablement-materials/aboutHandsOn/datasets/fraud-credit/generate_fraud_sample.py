#!/usr/bin/env python3
"""
Day 5(보험사 사기탐지) / Day 10(신용평가) 통합 시나리오용 합성 이진분류 데이터셋.

curriculum v1.0의 "보험사 사기탐지 모델 온보딩"·"신용평가 모델 E2E"에 쓸,
sklearn으로 바로 학습 가능한 작은 표 형식 데이터(CPU 친화).

컬럼:
  amount        거래/청구 금액
  age           고객 연령
  tenure_months 거래/계약 유지 개월
  num_claims    과거 청구 횟수
  credit_score  신용점수(300~900)
  distance_km   사고/거래 지점까지 거리
  channel       0=오프라인 1=온라인
  label         1=사기/부도 위험, 0=정상

사용:
  python generate_fraud_sample.py --rows 5000 --out fraud_sample.csv
"""
import argparse
import csv
import math
import random


def sigmoid(z):
    return 1.0 / (1.0 + math.exp(-z))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=5000)
    ap.add_argument("--out", default="fraud_sample.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    cols = ["amount", "age", "tenure_months", "num_claims",
            "credit_score", "distance_km", "channel", "label"]

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for _ in range(args.rows):
            amount = round(abs(rng.gauss(1200, 1500)), 2)
            age = rng.randint(19, 78)
            tenure = rng.randint(0, 180)
            num_claims = rng.choice([0, 0, 0, 1, 1, 2, 3, 5])
            credit = rng.randint(300, 900)
            distance = round(abs(rng.gauss(20, 40)), 1)
            channel = rng.randint(0, 1)

            # 위험 로짓: 큰 금액·많은 청구·낮은 신용·먼 거리·온라인일수록 위험↑
            z = (
                -3.2
                + 0.0006 * amount
                + 0.35 * num_claims
                - 0.004 * credit
                + 0.012 * distance
                + 0.4 * channel
                - 0.005 * tenure
            )
            p = sigmoid(z)
            label = 1 if rng.random() < p else 0
            w.writerow({
                "amount": amount, "age": age, "tenure_months": tenure,
                "num_claims": num_claims, "credit_score": credit,
                "distance_km": distance, "channel": channel, "label": label,
            })

    print(f"wrote {args.rows} rows -> {args.out}")


if __name__ == "__main__":
    main()
