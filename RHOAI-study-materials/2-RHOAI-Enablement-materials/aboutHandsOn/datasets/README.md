# 데이터셋

> 커리큘럼 실습용 소형 데이터(경로 체득용, 성능검증 아님). HF/Kaggle는 링크로.

| 폴더 | 파일 | 용도(Day) | 생성 |
|---|---|---|---|
| `iris/` | `iris.csv` (150행) | Day 6 RandomForest | sklearn iris (`export_iris.py`) |
| `fraud-credit/` | `fraud_sample.csv` (5000행) | Day 5 온보딩 / Day 10 신용평가 / Day 15 사기탐지 | 합성 이진분류 (`generate_fraud_sample.py`) |
| `guardrails/` | `pii_test_prompts.jsonl` (10건) | LLM 안전 테스트(선택) | PII·유해·인젝션 + benign |

## 원본 데이터셋 링크

- **MNIST (Day 2 PyTorch)**: torchvision 자동 다운로드 (`../models/train_mnist_pytorch.py`)
- **iris**: sklearn 내장
- **AI500 플랫폼 유스케이스 참고**: "Top Spotify Songs in 73 Countries" (Kaggle) — AI500(jukebox)이 쓰는 데이터. v0.9 커리큘럼 자체는 사용하지 않음.

## 재생성

```bash
python fraud-credit/generate_fraud_sample.py --rows 5000 --out fraud-credit/fraud_sample.csv
python iris/export_iris.py     # 워크벤치(sklearn) 환경에서
```
