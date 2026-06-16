from datetime import UTC, datetime
from sqlite3 import Connection
from time import sleep
from uuid import uuid4

import mlflow

from defect_detection.api.storage import save_retraining_job

RETRAINING_EXPERIMENT_NAME = "defect-detection-retraining-demo"


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
    }


def run_retraining_job(
    job: dict[str, object],
    database: Connection,
) -> None:
    job["status"] = "running"
    job["started_at"] = utc_now()
    job["message"] = "Retraining job is running."
    save_retraining_job(database, job)

    try:
        mlflow.set_experiment(RETRAINING_EXPERIMENT_NAME)

        with mlflow.start_run(run_name=f"demo-retraining-{job['job_id']}"):
            mlflow.log_param("job_id", job["job_id"])
            mlflow.log_param("trigger", "manual")
            mlflow.log_param("mode", "demo")
            mlflow.log_metric("demo_val_loss", 0.38)
            mlflow.log_metric("demo_dice_score", 0.74)
            mlflow.log_metric("demo_iou", 0.66)

            active_run = mlflow.active_run()

            if active_run is not None:
                job["mlflow_run_id"] = active_run.info.run_id

        sleep(1)

        job["status"] = "succeeded"
        job["message"] = "Retraining demo completed successfully."
    except Exception as exc:
        job["status"] = "failed"
        job["message"] = str(exc)
    finally:
        job["finished_at"] = utc_now()
        save_retraining_job(database, job)
