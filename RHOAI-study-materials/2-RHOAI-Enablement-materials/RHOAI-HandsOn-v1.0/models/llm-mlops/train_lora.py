#!/usr/bin/env python3
"""Fine-tune a small causal LM with LoRA and publish a merged model to S3."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import boto3
import torch
from datasets import load_dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
    set_seed,
)


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )


def split_s3_uri(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError(f"not an S3 URI: {uri}")
    return parsed.netloc, parsed.path.lstrip("/")


def download_prefix(client, uri: str, destination: Path) -> None:
    bucket, prefix = split_s3_uri(uri)
    prefix = prefix.rstrip("/") + "/"
    paginator = client.get_paginator("list_objects_v2")
    found = 0
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            key = item["Key"]
            if key.endswith("/"):
                continue
            relative = key[len(prefix) :]
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            client.download_file(bucket, key, str(target))
            found += 1
    if not found:
        raise FileNotFoundError(f"no objects found under {uri}")


def download_file(client, uri: str, destination: Path) -> None:
    bucket, key = split_s3_uri(uri)
    destination.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(bucket, key, str(destination))


def upload_tree(client, source: Path, uri: str) -> None:
    bucket, prefix = split_s3_uri(uri)
    prefix = prefix.rstrip("/")
    for path in source.rglob("*"):
        if path.is_file():
            key = f"{prefix}/{path.relative_to(source).as_posix()}"
            client.upload_file(str(path), bucket, key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-uri", required=True)
    parser.add_argument("--dataset-uri", required=True)
    parser.add_argument("--output-uri", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--max-length", type=int, default=384)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--lora-rank", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(42)
    client = s3_client()

    workspace = Path(tempfile.mkdtemp(prefix="week5-lora-"))
    model_dir = workspace / "base-model"
    dataset_path = workspace / "train.jsonl"
    adapter_dir = workspace / "adapter"
    merged_dir = workspace / "model"
    publish_dir = workspace / "publish"

    try:
        download_prefix(client, args.base_model_uri, model_dir)
        download_file(client, args.dataset_uri, dataset_path)

        tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        dtype = torch.bfloat16 if use_bf16 else torch.float16
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            local_files_only=True,
            torch_dtype=dtype,
            device_map={"": 0},
        )
        model.config.use_cache = False
        model = get_peft_model(
            model,
            LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=args.lora_rank,
                lora_alpha=args.lora_rank * 2,
                lora_dropout=0.05,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            ),
        )
        model.print_trainable_parameters()

        dataset = load_dataset("json", data_files=str(dataset_path), split="train")

        def tokenize(record):
            text = tokenizer.apply_chat_template(
                record["messages"], tokenize=False, add_generation_prompt=False
            )
            return tokenizer(text, truncation=True, max_length=args.max_length)

        tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)
        training_args = TrainingArguments(
            output_dir=str(adapter_dir),
            num_train_epochs=args.epochs,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            learning_rate=args.learning_rate,
            logging_steps=1,
            save_strategy="no",
            report_to="none",
            bf16=use_bf16,
            fp16=not use_bf16,
            remove_unused_columns=False,
        )
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized,
            data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        )
        result = trainer.train()
        model.save_pretrained(adapter_dir)

        merged = model.merge_and_unload()
        merged.save_pretrained(merged_dir, safe_serialization=True)
        tokenizer.save_pretrained(merged_dir)

        publish_dir.mkdir(parents=True)
        shutil.copytree(merged_dir, publish_dir / "model")
        shutil.copytree(adapter_dir, publish_dir / "adapter")
        metrics = {
            "run_id": args.run_id,
            "git_commit": args.git_commit,
            "base_model_uri": args.base_model_uri,
            "dataset_uri": args.dataset_uri,
            "model_uri": f"{args.output_uri.rstrip('/')}/model",
            "adapter_uri": f"{args.output_uri.rstrip('/')}/adapter",
            "samples": len(dataset),
            "epochs": args.epochs,
            "lora_rank": args.lora_rank,
            "train_loss": float(result.metrics["train_loss"]),
            "train_runtime": float(result.metrics["train_runtime"]),
        }
        (publish_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        upload_tree(client, publish_dir, args.output_uri)
        print(json.dumps(metrics, sort_keys=True))
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    main()

