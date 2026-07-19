# 데이터셋

> 폐쇄망 SNO에서 외부 접근 없이 경로를 체득하도록 **합성 샘플 + 생성 스크립트**를 둔다.
> 성능 검증용이 아니라 **서빙/파이프라인 경로 체득용**(작고 빠름).

| 폴더 | 파일 | 용도(Day) | 출처/생성 |
|---|---|---|---|
| `jukebox-spotify/` | `songs_sample.csv` (3000행) | AI500 재현(O1), Day7/8 | 합성. 원본=Kaggle "Top Spotify Songs in 73 Countries" |
| `jukebox-spotify/` | `generate_spotify_sample.py` | 재생성 | `--rows N --out file` |
| `fraud-credit/` | `fraud_sample.csv` (5000행) | Day5 사기탐지, Day10 신용평가 | 합성 이진분류 |
| `fraud-credit/` | `generate_fraud_sample.py` | 재생성 | — |
| `iris/` | `iris.csv` (150행) | Day6 RandomForest | sklearn iris |
| `iris/` | `export_iris.py` | 워크벤치 재생성 | `load_iris()` |
| `guardrails/` | `pii_test_prompts.jsonl` (10건) | Day13 Guardrails 검증 | PII·유해·인젝션 + benign |
| `_mnist_cache/` | `MNIST/raw/*` | Day4 PyTorch MNIST | torchvision MNIST 캐시 |
| `llm-support-sft/` | `train.jsonl` (24건) | Week5 LLM LoRA MLOps | 합성 한국어 운영지원 대화 |

## 원본 데이터셋 링크 (connected 시 실제 데이터)

- **Spotify (AI500 원본)**: <https://www.kaggle.com/datasets/asaniczka/top-spotify-songs-in-73-countries-daily-updated>
- **MNIST (Day4 PyTorch)**: `materials/datasets/_mnist_cache/MNIST/raw/`에 캐시. VM 기준 경로는 `/tmp/python3/datasets/_mnist_cache/MNIST/raw/`.
- **iris**: sklearn 내장

## MNIST 캐시 사용

Day4 PyTorch MNIST는 Python 패키지 문제가 아니라 학습 데이터셋이 필요하다. 폐쇄망/재현 테스트에서는 `torchvision.datasets.MNIST(..., download=False)`로 실행하고, root 경로를 다음 중 하나로 둔다.

```bash
# Bastion VM
/tmp/python3/datasets/_mnist_cache

# vault 자료 위치
materials/datasets/_mnist_cache
```

## jukebox 피처(원본 13개, 순서 유지)

`is_explicit, duration_ms, danceability, energy, key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo` → 타깃 `country`

## 재생성

```bash
python jukebox-spotify/generate_spotify_sample.py --rows 3000 --out jukebox-spotify/songs_sample.csv
python fraud-credit/generate_fraud_sample.py --rows 5000 --out fraud-credit/fraud_sample.csv
```
