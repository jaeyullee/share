#!/usr/bin/env python3
"""
AI500 jukebox 재현용 Spotify 합성 데이터셋 생성기.

원본(AI500)은 Kaggle "Top Spotify Songs in 73 Countries" 데이터를 쓴다.
  - https://www.kaggle.com/datasets/asaniczka/top-spotify-songs-in-73-countries-daily-updated
원본 컬럼/피처는 jukebox 3-prod_datascience/data_preprocessing.py 기준으로 13개:
  is_explicit, duration_ms, danceability, energy, key, loudness, mode,
  speechiness, acousticness, instrumentalness, liveness, valence, tempo
타깃: country (다중분류). 원본은 Keras Dense NN → ONNX export → KServe(OpenVINO) 서빙.

이 스크립트는 폐쇄망/오프라인 SNO에서 Kaggle 접근 없이도 서빙·파이프라인 경로를
체득할 수 있도록 같은 스키마의 소형 합성본을 만든다. (성능 검증용 아님, 경로 체득용)
국가별로 오디오 피처 분포를 살짝 다르게 줘서 모델이 학습할 신호를 만든다.

사용:
  python generate_spotify_sample.py --rows 3000 --out songs_sample.csv
"""
import argparse
import csv
import random

# 원본 13개 피처 순서를 그대로 유지(모델 입력 시그니처 호환 목적)
FEATURES = [
    "is_explicit", "duration_ms", "danceability", "energy", "key", "loudness",
    "mode", "speechiness", "acousticness", "instrumentalness", "liveness",
    "valence", "tempo",
]

# 소형 분류를 위해 5개국으로 축소(원본 73개국). country별로 분포 평균을 다르게 준다.
COUNTRY_PROFILES = {
    # country : (danceability_mu, energy_mu, valence_mu, tempo_mu, acousticness_mu, explicit_p)
    "US": (0.70, 0.72, 0.55, 122, 0.18, 0.45),
    "KR": (0.66, 0.74, 0.60, 118, 0.22, 0.10),
    "JP": (0.58, 0.68, 0.50, 130, 0.30, 0.08),
    "BR": (0.78, 0.70, 0.66, 115, 0.20, 0.30),
    "DE": (0.62, 0.66, 0.45, 126, 0.25, 0.25),
}


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def gen_row(country, rng):
    dm, em, vm, tm, am, ep = COUNTRY_PROFILES[country]
    return {
        "is_explicit": 1 if rng.random() < ep else 0,
        "duration_ms": int(rng.gauss(210000, 45000)),
        "danceability": round(clamp(rng.gauss(dm, 0.12)), 4),
        "energy": round(clamp(rng.gauss(em, 0.12)), 4),
        "key": rng.randint(0, 11),
        "loudness": round(rng.gauss(-7.0, 2.5), 3),
        "mode": rng.randint(0, 1),
        "speechiness": round(clamp(rng.gauss(0.08, 0.06), 0, 0.6), 4),
        "acousticness": round(clamp(rng.gauss(am, 0.12)), 4),
        "instrumentalness": round(clamp(rng.gauss(0.05, 0.1), 0, 1), 5),
        "liveness": round(clamp(rng.gauss(0.16, 0.1)), 4),
        "valence": round(clamp(rng.gauss(vm, 0.14)), 4),
        "tempo": round(clamp(rng.gauss(tm, 18), 50, 210), 3),
        "country": country,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=3000)
    ap.add_argument("--out", default="songs_sample.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    countries = list(COUNTRY_PROFILES.keys())
    cols = FEATURES + ["country"]

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for _ in range(args.rows):
            w.writerow(gen_row(rng.choice(countries), rng))

    print(f"wrote {args.rows} rows -> {args.out} (countries={countries})")


if __name__ == "__main__":
    main()
