# RHOAI-3.4-HandsOn-커리큘럼-v1.0.xlsx 추가 스터디
## week 5 - Step 1 폐쇄망 LLM artifact 준비

> **환경별 재확인**: model registry, Nexus와 S3 endpoint, bucket/prefix, base image digest와 반입 가능한 Python package version은 환경마다 다르다. 다운로드·반입 전에 실제 값을 확인한다. 공통 경계 조건은 [실습자료 검토 항목](<00-실습자료-검토항목.md#환경별-재확인>)을 참고한다.

> 사전 활성화: [Week5 Step 0 사전점검](<Week5-Step0 사전점검 실습.md>)을 완료한다.

훈련 입력인 base model과 dataset을 S3에 버전 고정하고, 커스텀 training image가 추가로 설치할 `boto3` wheel을 Nexus에 준비한다.

### boto3 wheel 반입

인터넷 접근이 가능한 환경에서 Python 3.12용 wheel과 전이 의존성을 받는다.

```bash
deactivate 2>/dev/null || true
rm -rf /tmp/week5-pypi-upload-venv
/usr/bin/python3 -m venv /tmp/week5-pypi-upload-venv
source /tmp/week5-pypi-upload-venv/bin/activate
python -m pip install --upgrade pip 'twine==5.0.0' 'pkginfo==1.12.1.2'

rm -rf /tmp/week5-boto3-wheels
mkdir -p /tmp/week5-boto3-wheels

python -m pip download --only-binary=:all: \
  --python-version 312 \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --dest /tmp/week5-boto3-wheels \
  'boto3==1.40.18'
```

Week5 전용 업로드 venv를 다시 활성화하고 Nexus hosted repository에 업로드한다.

```bash
source /tmp/week5-pypi-upload-venv/bin/activate

python -m twine upload \
  --repository-url http://192.168.10.50:8081/repository/pypi-hosted/ \
  -u <NEXUS_ID> -p '<NEXUS_PW>' \
  /tmp/week5-boto3-wheels/*

curl -fsS \
  http://192.168.10.50:8081/repository/pypi-hosted/simple/boto3/ | \
  grep 'boto3-1.40.18'

deactivate 2>/dev/null || true
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
  --path /models/:/tmp/week5-qwen-base \
  192.168.10.50:5010/models/qwen2.5-0.5b-instruct:7ae5576

find /tmp/week5-qwen-base -maxdepth 2 -type f | sort
test -s /tmp/week5-qwen-base/config.json
test -s /tmp/week5-qwen-base/model.safetensors
```

`config.json`, tokenizer 파일과 safetensors가 있어야 한다. `/models` 아래에 한 단계 디렉터리가 더 생겼다면 실제 모델 파일이 있는 디렉터리를 다음 `BASE_DIR`로 지정한다.

### S3에 버전 고정

```bash
cd /tmp/python3

export RHOAI_HANDSON_DIR="$PWD"
test -f "$RHOAI_HANDSON_DIR/datasets/llm-support-sft/train.jsonl"

mc alias set truenas http://192.168.20.5:9000 \
  '<MINIO_ID>' '<MINIO_PW>'

mc mb --ignore-existing truenas/rhoai-llm-mlops

BASE_DIR=/tmp/week5-qwen-base
mc mirror --overwrite "$BASE_DIR" \
  truenas/rhoai-llm-mlops/base/qwen2.5-0.5b-instruct/

mc cp "$RHOAI_HANDSON_DIR/datasets/llm-support-sft/train.jsonl" \
  truenas/rhoai-llm-mlops/datasets/support/v1/train.jsonl

mc ls --recursive truenas/rhoai-llm-mlops/base/qwen2.5-0.5b-instruct/
mc stat truenas/rhoai-llm-mlops/datasets/support/v1/train.jsonl

rm -f /tmp/week5-model-auth.json
```

### 재현성 기록

```bash
sha256sum "$RHOAI_HANDSON_DIR/datasets/llm-support-sft/train.jsonl"
mc stat --json \
  truenas/rhoai-llm-mlops/datasets/support/v1/train.jsonl | jq .
```

실제 운영에서는 dataset object version 또는 digest, base ModelCar digest와 license 승인 정보를 모델 버전에 함께 기록한다.

### 확인 기준

- Nexus에서 `boto3==1.40.18`과 전이 wheel을 조회할 수 있다.
- S3 base model prefix에 config, tokenizer와 weight 파일이 있다.
- dataset은 24개 JSONL record이며 S3 object로 존재한다.
- registry 인증 파일이 `/tmp`에 남지 않는다.

### Python venv 종료
```bash
deactivate 2>/dev/null || true
```
