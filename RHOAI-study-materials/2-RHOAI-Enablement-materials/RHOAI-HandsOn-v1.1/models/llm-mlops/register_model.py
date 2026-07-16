#!/usr/bin/env python3
"""Idempotently register a fine-tuned model version in Model Registry v1alpha3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


def string_property(value: str) -> dict:
    return {"metadataType": "MetadataStringValue", "string_value": value}


def double_property(value: float) -> dict:
    return {"metadataType": "MetadataDoubleValue", "double_value": float(value)}


def request(session, method: str, url: str, **kwargs) -> dict:
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code not in {200, 201}:
        raise RuntimeError(f"{method} {url}: {response.status_code} {response.text}")
    return response.json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-url", required=True)
    parser.add_argument("--model-name", default="support-assistant")
    parser.add_argument("--version-name", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--metrics-path", type=Path, required=True)
    parser.add_argument("--result-path", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_uri = f"{args.output_prefix.rstrip('/')}/{args.run_id}/model"
    base = args.registry_url.rstrip("/") + "/api/model_registry/v1alpha3"
    session = requests.Session()
    models = request(session, "GET", f"{base}/registered_models").get("items", [])
    registered = next((item for item in models if item["name"] == args.model_name), None)
    if registered is None:
        registered = request(
            session,
            "POST",
            f"{base}/registered_models",
            json={
                "name": args.model_name,
                "description": "Week 5 support assistant LoRA model",
                "state": "LIVE",
            },
        )

    versions = request(session, "GET", f"{base}/model_versions").get("items", [])
    version = next(
        (
            item
            for item in versions
            if item.get("registeredModelId") == registered["id"]
            and item["name"] == args.version_name
        ),
        None,
    )
    metrics = json.loads(args.metrics_path.read_text(encoding="utf-8"))
    if version is None:
        version = request(
            session,
            "POST",
            f"{base}/model_versions",
            json={
                "name": args.version_name,
                "registeredModelId": registered["id"],
                "description": "Fine-tuned by the Week 5 KFP pipeline",
                "state": "LIVE",
                "customProperties": {
                    "stage": string_property("Staging"),
                    "git_commit": string_property(args.git_commit),
                    "train_loss": double_property(metrics["train_loss"]),
                    "train_runtime": double_property(metrics["train_runtime"]),
                },
            },
        )
        request(
            session,
            "POST",
            f"{base}/model_versions/{version['id']}/artifacts",
            json={
                "name": f"{args.model_name}-{args.version_name}",
                "description": "Merged Transformers model for vLLM serving",
                "uri": model_uri,
                "state": "LIVE",
                "modelFormatName": "vLLM",
                "modelFormatVersion": "1",
                "artifactType": "model-artifact",
            },
        )

    result = {
        "registered_model_id": registered["id"],
        "model_version_id": version["id"],
        "model_uri": model_uri,
        "stage": "Staging",
    }
    args.result_path.parent.mkdir(parents=True, exist_ok=True)
    args.result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
