#!/usr/bin/env python3
"""Create a Kubeflow Trainer v2 TrainJob, wait, and emit KFP Metrics metadata."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import boto3
from kubernetes import client, config


GROUP = "trainer.kubeflow.org"
VERSION = "v1alpha1"
PLURAL = "trainjobs"


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-z0-9-]", "-", value.lower()).strip("-")
    return f"llm-lora-{value[:40]}".rstrip("-")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--training-image", required=True)
    parser.add_argument("--base-model-uri", required=True)
    parser.add_argument("--dataset-uri", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--metrics-path", required=True)
    parser.add_argument("--executor-input", required=True)
    parser.add_argument("--timeout", type=int, default=7200)
    return parser.parse_args()


def trainjob_body(args: argparse.Namespace) -> dict:
    output_uri = f"{args.output_prefix.rstrip('/')}/{args.run_id}"
    env = [
        {
            "name": key,
            "valueFrom": {"secretKeyRef": {"name": "llm-s3", "key": key}},
        }
        for key in (
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_ENDPOINT_URL",
            "AWS_DEFAULT_REGION",
        )
    ]
    return {
        "apiVersion": f"{GROUP}/{VERSION}",
        "kind": "TrainJob",
        "metadata": {
            "name": safe_name(args.run_id),
            "namespace": args.namespace,
            "labels": {
                "app.kubernetes.io/part-of": "week5-llm-mlops",
                "mlops.opendatahub.io/git-commit": args.git_commit[:40],
            },
        },
        "spec": {
            "runtimeRef": {
                "apiGroup": GROUP,
                "kind": "ClusterTrainingRuntime",
                "name": "torch-distributed-cuda130-torch210-py312",
            },
            "trainer": {
                "image": args.training_image,
                "command": ["python", "/opt/llm-mlops/train_lora.py"],
                "args": [
                    "--base-model-uri", args.base_model_uri,
                    "--dataset-uri", args.dataset_uri,
                    "--output-uri", output_uri,
                    "--run-id", args.run_id,
                    "--git-commit", args.git_commit,
                    "--epochs", str(args.epochs),
                ],
                "env": env,
                "numNodes": 1,
                "numProcPerNode": 1,
                "resourcesPerNode": {
                    "requests": {"cpu": "4", "memory": "12Gi", "nvidia.com/gpu": "1"},
                    "limits": {"cpu": "8", "memory": "24Gi", "nvidia.com/gpu": "1"},
                },
            },
            "podTemplateOverrides": [
                {
                    "targetJobs": ["node"],
                    "spec": {
                        "serviceAccountName": "llm-trainer",
                        "nodeSelector": {"lab-role": "gpu"},
                        "imagePullSecrets": [{"name": "model-registry-pull"}],
                    },
                }
            ],
        },
    }


def emit_metrics(args: argparse.Namespace, metrics: dict) -> None:
    path = Path(args.metrics_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    executor_input = json.loads(args.executor_input)
    output_path = Path(executor_input["outputs"]["outputFile"])
    artifact = executor_input["outputs"]["artifacts"]["metrics"]["artifacts"][0]
    runtime_artifact = {
        "name": artifact["name"],
        "uri": artifact["uri"],
        "metadata": {
            "train_loss": float(metrics["train_loss"]),
            "train_runtime": float(metrics["train_runtime"]),
            "samples": float(metrics["samples"]),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"artifacts": {"metrics": {"artifacts": [runtime_artifact]}}}),
        encoding="utf-8",
    )


def fetch_metrics(output_uri: str) -> dict:
    parsed = urlparse(output_uri)
    key = f"{parsed.path.lstrip('/').rstrip('/')}/metrics.json"
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
    response = s3.get_object(Bucket=parsed.netloc, Key=key)
    return json.loads(response["Body"].read())


def main() -> None:
    args = parse_args()
    config.load_incluster_config()
    api = client.CustomObjectsApi()
    body = trainjob_body(args)
    name = body["metadata"]["name"]

    try:
        api.create_namespaced_custom_object(GROUP, VERSION, args.namespace, PLURAL, body)
    except client.ApiException as exc:
        if exc.status != 409:
            raise

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        job = api.get_namespaced_custom_object(GROUP, VERSION, args.namespace, PLURAL, name)
        conditions = job.get("status", {}).get("conditions", [])
        for condition in conditions:
            if condition.get("status") != "True":
                continue
            if condition.get("type") in {"Complete", "Succeeded"}:
                output_uri = f"{args.output_prefix.rstrip('/')}/{args.run_id}"
                emit_metrics(args, fetch_metrics(output_uri))
                print(f"trainjob={name} status={condition['type']}")
                return
            if condition.get("type") in {"Failed", "Failure"}:
                raise RuntimeError(json.dumps(condition))
        time.sleep(15)
    raise TimeoutError(f"TrainJob {name} did not complete in {args.timeout} seconds")


if __name__ == "__main__":
    main()
