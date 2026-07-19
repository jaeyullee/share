#!/usr/bin/env python3
"""Compile the Week 5 pipeline as Kubernetes-native Pipeline resources."""

import argparse
import os

from kfp import compiler, dsl, kubernetes
from kfp.compiler.compiler_utils import KubernetesManifestOptions


RUNTIME_IMAGE = os.environ.get(
    "RUNTIME_IMAGE",
    "192.168.10.50:5010/rhoai-training/llm-lora-runtime:replace-me",
)


@dsl.container_component
def train_model(
    namespace: str,
    run_id: str,
    git_commit: str,
    training_image: str,
    base_model_uri: str,
    dataset_uri: str,
    output_prefix: str,
    epochs: float,
    metrics: dsl.Output[dsl.Metrics],
):
    return dsl.ContainerSpec(
        image=RUNTIME_IMAGE,
        command=["python", "/opt/llm-mlops/submit_trainjob.py"],
        args=[
            "--namespace", namespace,
            "--run-id", run_id,
            "--git-commit", git_commit,
            "--training-image", training_image,
            "--base-model-uri", base_model_uri,
            "--dataset-uri", dataset_uri,
            "--output-prefix", output_prefix,
            "--epochs", epochs,
            "--metrics-path", metrics.path,
            "--executor-input", dsl.PIPELINE_TASK_EXECUTOR_INPUT_PLACEHOLDER,
        ],
    )


@dsl.container_component
def register_model(
    registry_url: str,
    model_name: str,
    version_name: str,
    git_commit: str,
    output_prefix: str,
    run_id: str,
    metrics: dsl.Input[dsl.Metrics],
    registration: dsl.Output[dsl.Artifact],
):
    return dsl.ContainerSpec(
        image=RUNTIME_IMAGE,
        command=["python", "/opt/llm-mlops/register_model.py"],
        args=[
            "--registry-url", registry_url,
            "--model-name", model_name,
            "--version-name", version_name,
            "--git-commit", git_commit,
            "--output-prefix", output_prefix,
            "--run-id", run_id,
            "--metrics-path", metrics.path,
            "--result-path", registration.path,
        ],
    )


@dsl.pipeline(name="support-assistant-lora")
def llm_pipeline(
    namespace: str = "rhoai-llm-mlops",
    run_id: str = "manual-v1",
    git_commit: str = "manual",
    training_image: str = RUNTIME_IMAGE,
    base_model_uri: str = "s3://rhoai-llm-mlops/base/qwen2.5-0.5b-instruct",
    dataset_uri: str = "s3://rhoai-llm-mlops/datasets/support/v1/train.jsonl",
    output_prefix: str = "s3://rhoai-llm-mlops/models/support-assistant",
    registry_url: str = "http://jukebox-registry.rhoai-model-registries.svc:8080",
    epochs: float = 1.0,
):
    trained = train_model(
        namespace=namespace,
        run_id=run_id,
        git_commit=git_commit,
        training_image=training_image,
        base_model_uri=base_model_uri,
        dataset_uri=dataset_uri,
        output_prefix=output_prefix,
        epochs=epochs,
    )
    kubernetes.set_image_pull_secrets(trained, ["model-registry-pull"])
    kubernetes.use_secret_as_env(
        trained,
        secret_name="llm-s3",
        secret_key_to_env={
            "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
            "AWS_ENDPOINT_URL": "AWS_ENDPOINT_URL",
            "AWS_DEFAULT_REGION": "AWS_DEFAULT_REGION",
        },
    )

    registered = register_model(
        registry_url=registry_url,
        model_name="support-assistant",
        version_name=run_id,
        git_commit=git_commit,
        output_prefix=output_prefix,
        run_id=run_id,
        metrics=trained.outputs["metrics"],
    )
    kubernetes.set_image_pull_secrets(registered, ["model-registry-pull"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", default="rhoai-llm-mlops")
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    compiler.Compiler().compile(
        pipeline_func=llm_pipeline,
        package_path=args.output,
        kubernetes_manifest_format=True,
        kubernetes_manifest_options=KubernetesManifestOptions(
            pipeline_name="support-assistant-lora",
            pipeline_display_name="Support Assistant LoRA",
            pipeline_version_name=f"support-assistant-lora-{args.version}",
            pipeline_version_display_name=f"Support Assistant LoRA {args.version}",
            namespace=args.namespace,
            include_pipeline_manifest=True,
        ),
    )


if __name__ == "__main__":
    main()
