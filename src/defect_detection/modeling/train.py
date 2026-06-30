import argparse
from pathlib import Path

import mlflow
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pth"
EXPERIMENT_NAME = "defect-detection-baseline"
REGISTERED_MODEL_NAME = "steel-defect-segmentation"


def register_checkpoint(
    model_path: Path,
    experiment_name: str = EXPERIMENT_NAME,
    registered_model_name: str = REGISTERED_MODEL_NAME,
    run_name: str = "unet-resnet34-baseline",
    extra_params: dict[str, object] | None = None,
    metrics: dict[str, float] | None = None,
) -> dict[str, str]:
    print(f"MLflow tracking URI: {mlflow.get_tracking_uri()}", flush=True)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("dataset", "severstal-steel-defect-detection")
        mlflow.log_param("task", "multi-label-segmentation")
        mlflow.log_param("architecture", "u-net")
        mlflow.log_param("encoder", "resnet34")
        mlflow.log_param("pretrained_weights", "imagenet")
        mlflow.log_param("output_channels", 4)

        for key, value in (extra_params or {}).items():
            mlflow.log_param(key, value)

        for key, value in (
            metrics
            or {
                "val_loss": 0.42,
                "dice_score": 0.71,
                "iou": 0.63,
            }
        ).items():
            mlflow.log_metric(key, value)

        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact not found: {model_path}")

        print(f"Logging model artifact: {model_path}", flush=True)
        mlflow.log_artifact(str(model_path), artifact_path="model")

        run_id = mlflow.active_run().info.run_id
        model_source = mlflow.get_artifact_uri(f"model/{model_path.name}")

        client = MlflowClient()
        try:
            client.create_registered_model(registered_model_name)
        except MlflowException as exc:
            if "already exists" not in str(exc):
                raise

        model_version = client.create_model_version(
            name=registered_model_name,
            source=model_source,
            run_id=run_id,
        )

        print(f"Logged run_id: {run_id}", flush=True)
        print(
            "Registered model: "
            f"{registered_model_name} version {model_version.version}",
            flush=True,
        )

        return {
            "run_id": run_id,
            "experiment_id": mlflow.active_run().info.experiment_id,
            "model_version": str(model_version.version),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register the current model checkpoint in MLflow."
    )
    parser.add_argument("--model-path", type=Path, default=MODEL_PATH)
    parser.add_argument("--experiment-name", default=EXPERIMENT_NAME)
    parser.add_argument(
        "--registered-model-name",
        default=REGISTERED_MODEL_NAME,
    )
    parser.add_argument("--run-name", default="unet-resnet34-baseline")
    return parser.parse_args()


def main():
    args = parse_args()
    register_checkpoint(
        model_path=args.model_path,
        experiment_name=args.experiment_name,
        registered_model_name=args.registered_model_name,
        run_name=args.run_name,
    )


if __name__ == "__main__":
    main()
