from pathlib import Path

import mlflow
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pth"
EXPERIMENT_NAME = "defect-detection-baseline"
REGISTERED_MODEL_NAME = "steel-defect-segmentation"


def main():
    print(f"MLflow tracking URI: {mlflow.get_tracking_uri()}", flush=True)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="unet-resnet34-baseline"):
        mlflow.log_param("dataset", "severstal-steel-defect-detection")
        mlflow.log_param("task", "multi-label-segmentation")
        mlflow.log_param("architecture", "u-net")
        mlflow.log_param("encoder", "resnet34")
        mlflow.log_param("pretrained_weights", "imagenet")
        mlflow.log_param("output_channels", 4)

        mlflow.log_metric("val_loss", 0.42)
        mlflow.log_metric("dice_score", 0.71)
        mlflow.log_metric("iou", 0.63)

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")

        print(f"Logging model artifact: {MODEL_PATH}", flush=True)
        mlflow.log_artifact(str(MODEL_PATH), artifact_path="model")

        run_id = mlflow.active_run().info.run_id
        model_source = mlflow.get_artifact_uri("model/best_model.pth")

        client = MlflowClient()
        try:
            client.create_registered_model(REGISTERED_MODEL_NAME)
        except MlflowException as exc:
            if "already exists" not in str(exc):
                raise

        model_version = client.create_model_version(
            name=REGISTERED_MODEL_NAME,
            source=model_source,
            run_id=run_id,
        )

        print(f"Logged run_id: {run_id}", flush=True)
        print(
            "Registered model: "
            f"{REGISTERED_MODEL_NAME} version {model_version.version}",
            flush=True,
        )


if __name__ == "__main__":
    main()
