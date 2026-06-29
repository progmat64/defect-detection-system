import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DATABASE_PATH = Path("storage/app.db")
PREDICTION_HISTORY_LIMIT = 50
RETRAINING_JOB_HISTORY_LIMIT = 10


def connect_database(path: Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    initialize_database(connection)
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            filename TEXT,
            content_type TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            image_preview TEXT NOT NULL,
            predicted_classes TEXT NOT NULL,
            has_any_defect INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            true_classes TEXT NOT NULL,
            is_mismatch INTEGER NOT NULL,
            FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
        );

        CREATE TABLE IF NOT EXISTS retraining_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            message TEXT NOT NULL,
            mlflow_run_id TEXT,
            mlflow_experiment_id TEXT
        );
        """
    )
    _ensure_column(
        connection,
        "retraining_jobs",
        "mlflow_experiment_id",
        "TEXT",
    )
    connection.commit()


def save_prediction(
    connection: sqlite3.Connection,
    item: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT OR REPLACE INTO predictions (
            prediction_id,
            created_at,
            filename,
            content_type,
            size_bytes,
            image_preview,
            predicted_classes,
            has_any_defect
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item["prediction_id"],
            item["created_at"],
            item["filename"],
            item["content_type"],
            item["size_bytes"],
            item["image_preview"],
            json.dumps(item["predicted_classes"]),
            int(item["has_any_defect"]),
        ),
    )
    connection.commit()


def list_predictions(
    connection: sqlite3.Connection,
    limit: int = PREDICTION_HISTORY_LIMIT,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            prediction_id,
            created_at,
            filename,
            content_type,
            size_bytes,
            image_preview,
            predicted_classes,
            has_any_defect
        FROM predictions
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return [_prediction_from_row(row) for row in rows]


def get_prediction_classes(
    connection: sqlite3.Connection,
    prediction_id: str,
) -> list[int] | None:
    row = connection.execute(
        "SELECT predicted_classes FROM predictions WHERE prediction_id = ?",
        (prediction_id,),
    ).fetchone()

    if row is None:
        return None

    return json.loads(row["predicted_classes"])


def save_feedback(
    connection: sqlite3.Connection,
    prediction_id: str,
    created_at: str,
    true_classes: list[int],
    is_mismatch: bool,
) -> None:
    connection.execute(
        """
        INSERT INTO feedback (
            prediction_id,
            created_at,
            true_classes,
            is_mismatch
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            prediction_id,
            created_at,
            json.dumps(true_classes),
            int(is_mismatch),
        ),
    )
    connection.commit()


def get_feedback_totals(connection: sqlite3.Connection) -> tuple[int, int]:
    row = connection.execute(
        """
        SELECT
            COUNT(*) AS feedback_total,
            COALESCE(SUM(is_mismatch), 0) AS mismatch_total
        FROM feedback
        """
    ).fetchone()

    return int(row["feedback_total"]), int(row["mismatch_total"])


def save_retraining_job(
    connection: sqlite3.Connection,
    job: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT OR REPLACE INTO retraining_jobs (
            job_id,
            status,
            created_at,
            started_at,
            finished_at,
            message,
            mlflow_run_id,
            mlflow_experiment_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job["job_id"],
            job["status"],
            job["created_at"],
            job["started_at"],
            job["finished_at"],
            job["message"],
            job["mlflow_run_id"],
            job["mlflow_experiment_id"],
        ),
    )
    connection.commit()


def get_retraining_job(
    connection: sqlite3.Connection,
    job_id: str,
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            job_id,
            status,
            created_at,
            started_at,
            finished_at,
            message,
            mlflow_run_id,
            mlflow_experiment_id
        FROM retraining_jobs
        WHERE job_id = ?
        """,
        (job_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def list_retraining_jobs(
    connection: sqlite3.Connection,
    limit: int = RETRAINING_JOB_HISTORY_LIMIT,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            job_id,
            status,
            created_at,
            started_at,
            finished_at,
            message,
            mlflow_run_id,
            mlflow_experiment_id
        FROM retraining_jobs
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return [dict(row) for row in rows]


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})")
    }

    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )


def _prediction_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "prediction_id": row["prediction_id"],
        "created_at": row["created_at"],
        "filename": row["filename"],
        "content_type": row["content_type"],
        "size_bytes": row["size_bytes"],
        "image_preview": row["image_preview"],
        "predicted_classes": json.loads(row["predicted_classes"]),
        "has_any_defect": bool(row["has_any_defect"]),
    }
