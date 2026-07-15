# RHOAI-3.4-HandsOn-커리큘럼-v1.1.xlsx 추가 스터디
## week 5 - Step 1 폐쇄망 LLM artifact 준비

> 사전 활성화: [Week5 Step 0 사전점검](Week5-Step0%20사전점검%20실습.md)을 완료한다.

훈련 입력인 base model과 dataset을 S3에 버전 고정하고, 커스텀 training image가 추가로 설치할 `boto3` wheel을 Nexus에 준비한다.

### boto3 wheel 반입

인터넷 접근이 가능한 환경에서 Python 3.12용 wheel과 전이 의존성을 받는다.

```bash
rm -rf /tmp/week5-boto3-wheels
mkdir -p /tmp/week5-boto3-wheels

python3 -m pip download --only-binary=:all: \
  --python-version 312 \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --dest /tmp/week5-boto3-wheels \
  'boto3==1.40.18'
```

기존 Day3의 `pypi-upload-venv`를 활성화하고 Nexus hosted repository에 업로드한다.

```bash
source /tmp/pypi-upload-venv/bin/activate

twine upload \
  --repository-url http://192.168.10.50:8081/repository/pypi-hosted/ \
  -u <NEXUS_ID> -p '<NEXUS_PW>' \
  /tmp/week5-boto3-wheels/*

curl -fsS \
  http://192.168.10.50:8081/repository/pypi-hosted/simple/boto3/ | \
  grep 'boto3-1.40.18'
```

### ModelCar에서 base model 추출

Day14에서 사용한 Qwen2.5 0.5B ModelCar의 immutable tag를 사용한다. registry 인증 파일은 `/tmp`에만 만들고 작업 후 삭제한다.

```bash
rm -rf /tmp/week5-qwen-base
mkdir -p /tmp/week5-qwen-base

podman login --tls-verify=false \
  --authfile /tmp/week5-model-auth.json \
  -u '<MODEL_REGISTRY_ID>' -p '<MODEL_REGISTRY_PW>' \
  192.168.10.50:5010

REGISTRY_AUTH_FILE=/tmp/week5-model-auth.json \
oc image extract --confirm \
  --path /models:/tmp/week5-qwen-base \
  192.168.10.50:5010/models/qwen2.5-0.5b-instruct:7ae5576

find /tmp/week5-qwen-base -maxdepth 2 -type f | sort
```

`config.json`, tokenizer 파일과 safetensors가 있어야 한다. `/models` 아래에 한 단계 디렉터리가 더 생겼다면 실제 모델 파일이 있는 디렉터리를 다음 `BASE_DIR`로 지정한다.

### S3에 버전 고정

```bash
mc alias set truenas http://192.168.20.5:9000 \
  '<MINIO_ID>' '<MINIO_PW>'

mc mb --ignore-existing truenas/rhoai-llm-mlops

BASE_DIR=/tmp/week5-qwen-base
mc mirror --overwrite "$BASE_DIR" \
  truenas/rhoai-llm-mlops/base/qwen2.5-0.5b-instruct/

mc cp /tmp/python3/datasets/llm-support-sft/train.jsonl \
  truenas/rhoai-llm-mlops/datasets/support/v1/train.jsonl

mc ls --recursive truenas/rhoai-llm-mlops/base/qwen2.5-0.5b-instruct/
mc stat truenas/rhoai-llm-mlops/datasets/support/v1/train.jsonl

rm -f /tmp/week5-model-auth.json
```

### 재현성 기록

```bash
sha256sum /tmp/python3/datasets/llm-support-sft/train.jsonl
mc stat --json \
  truenas/rhoai-llm-mlops/datasets/support/v1/train.jsonl | jq .
```

실제 운영에서는 dataset object version 또는 digest, base ModelCar digest와 license 승인 정보를 모델 버전에 함께 기록한다.

### 확인 기준

- Nexus에서 `boto3==1.40.18`과 전이 wheel을 조회할 수 있다.
- S3 base model prefix에 config, tokenizer와 weight 파일이 있다.
- dataset은 24개 JSONL record이며 S3 object로 존재한다.
- registry 인증 파일이 `/tmp`에 남지 않는다.
