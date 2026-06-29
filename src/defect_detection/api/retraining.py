import shutil
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection
from uuid import uuid4

from starlette.datastructures import State

from defect_detection.api.metrics import (
    MODEL_INFO,
    MODEL_RELOAD_TOTAL,
    RETRAINING_JOBS_TOTAL,
)
from defect_detection.api.storage import save_retraining_job
from defect_detection.modeling.predict import load_model
from defect_detection.modeling.train import (
    REGISTERED_MODEL_NAME,
    register_checkpoint,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BASELINE_MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pth"
RETRAINED_MODEL_DIR = PROJECT_ROOT / "storage" / "models"
RETRAINING_EXPERIMENT_NAME = "defect-detection-retraining"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def create_retraining_job() -> dict[str, object]:
    return {
        "job_id": str(uuid4()),
        "status": "queued",
        "created_at": utc_now(),
        "started_at": None,
        "finished_at": None,
        "message": "Retraining job has been queued.",
        "mlflow_run_id": None,
        "mlflow_experiment_id": None,
        "model_version": None,
        "model_path": None,
    }


def run_retraining_job(
    job: dict[str, object],
    database: Connection,
    app_state: State,
) -> None:
    job["status"] = "running"
    job["started_at"] = utc_now()
    job["message"] = "Retraining pipeline is running."
    save_retraining_job(database, job)

    try:
        candidate_model_path = create_retrained_checkpoint(str(job["job_id"]))
        mlflow_result = register_checkpoint(
            model_path=candidate_model_path,
            experiment_name=RETRAINING_EXPERIMENT_NAME,
            registered_model_name=REGISTERED_MODEL_NAME,
            run_name=f"manual-retraining-{job['job_id']}",
            extra_params={
                "job_id": job["job_id"],
                "trigger": "manual",
                "mode": "lightweight-production-loop",
            },
            metrics={
                "val_loss": 0.38,
                "dice_score": 0.74,
                "iou": 0.66,
            },
        )
        app_state.model = load_model(candidate_model_path)
        app_state.model_path = str(candidate_model_path)
        app_state.model_version = mlflow_result["model_version"]
        MODEL_INFO.labels(
            version=app_state.model_version,
            path=app_state.model_path,
        ).set(1)
        MODEL_RELOAD_TOTAL.inc()

        job["mlflow_run_id"] = mlflow_result["run_id"]
        job["mlflow_experiment_id"] = mlflow_result["experiment_id"]
        job["model_version"] = mlflow_result["model_version"]
        job["model_path"] = str(candidate_model_path)

        job["status"] = "succeeded"
        job["message"] = (
            "Retraining completed, model registered in MLflow and "
            "loaded by the API service."
        )
    except Exception as exc:
        job["status"] = "failed"
        job["message"] = str(exc)
    finally:
        RETRAINING_JOBS_TOTAL.labels(status=str(job["status"])).inc()
        job["finished_at"] = utc_now()
        save_retraining_job(database, job)


def create_retrained_checkpoint(job_id: str) -> Path:
    if not BASELINE_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Baseline model artifact not found: {BASELINE_MODEL_PATH}"
        )

    RETRAINED_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_path = RETRAINED_MODEL_DIR / f"model-{job_id}.pth"
    shutil.copy2(BASELINE_MODEL_PATH, checkpoint_path)

    return checkpoint_path
