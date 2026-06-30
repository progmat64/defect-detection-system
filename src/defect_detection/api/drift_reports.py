import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
    Response,
)

from defect_detection.api.retraining import (
    create_retraining_job,
    run_retraining_job,
)
from defect_detection.api.storage import (
    list_recent_prediction_features,
    save_retraining_job,
)
from defect_detection.monitoring.evidently_drift import (
    REPORT_FILENAME_PREFIX,
    generate_report_file,
)
from defect_detection.monitoring.report import (
    generate_markdown_report,
    save_markdown_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DRIFT_REPORTS_DIR = PROJECT_ROOT / "reports" / "drift"
REPORT_FILENAME_RE = re.compile(
    r"^drift_report_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.md$"
)
EVIDENTLY_REPORT_FILENAME_RE = re.compile(
    rf"^{REPORT_FILENAME_PREFIX}\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}}"
    r"\.html$"
)

drift_reports_router = APIRouter(prefix="/drift/reports")


@drift_reports_router.post("/evidently")
def create_evidently_report(
    request: Request,
    background_tasks: BackgroundTasks,
    auto_retrain: bool = False,
) -> dict[str, Any]:
    reference_frame = getattr(
        request.app.state, "reference_features", None
    )
    if reference_frame is None:
        raise HTTPException(
            status_code=503,
            detail="Reference feature table is not loaded.",
        )

    current_records = list_recent_prediction_features(request.app.state.db)

    try:
        report_path, summary = generate_report_file(
            reference_frame,
            current_records,
            DRIFT_REPORTS_DIR,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    retraining_triggered = False
    if auto_retrain and summary["dataset_drift"]:
        job = create_retraining_job()
        job["message"] = (
            "Retraining auto-triggered by Evidently data drift detection."
        )
        save_retraining_job(request.app.state.db, job)
        background_tasks.add_task(
            run_retraining_job,
            job,
            request.app.state.db,
            request.app.state,
        )
        retraining_triggered = True

    return {
        "filename": report_path.name,
        "created_at": parse_evidently_timestamp(report_path.name),
        "sample_size": len(current_records),
        "summary": summary,
        "retraining_triggered": retraining_triggered,
    }


@drift_reports_router.get("/evidently/{filename}")
def read_evidently_report(filename: str) -> Response:
    report_path = resolve_evidently_report_path(filename)
    return Response(
        content=report_path.read_text(encoding="utf-8"),
        media_type="text/html; charset=utf-8",
    )


@drift_reports_router.get("")
def list_drift_reports() -> dict[str, list[dict[str, Any]]]:
    return {"items": list_drift_report_items()}


@drift_reports_router.post("")
def create_drift_report(request: Request) -> dict[str, Any]:
    status = build_drift_status_snapshot(request)
    report_path = save_markdown_report(
        generate_markdown_report(status),
        DRIFT_REPORTS_DIR,
    )

    return drift_report_item(report_path)


@drift_reports_router.get("/{filename}")
def read_drift_report(filename: str) -> Response:
    report_path = resolve_report_path(filename)
    return Response(
        content=report_path.read_text(encoding="utf-8"),
        media_type="text/markdown; charset=utf-8",
    )


@drift_reports_router.get("/{filename}/download")
def download_drift_report(filename: str) -> Response:
    report_path = resolve_report_path(filename)
    return Response(
        content=report_path.read_text(encoding="utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{report_path.name}"'
        },
    )


def list_drift_report_items() -> list[dict[str, Any]]:
    if not DRIFT_REPORTS_DIR.exists():
        return []

    return [
        drift_report_item(path)
        for path in sorted(
            DRIFT_REPORTS_DIR.glob("drift_report_*.md"),
            reverse=True,
        )
        if REPORT_FILENAME_RE.match(path.name)
    ]


def drift_report_item(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    summary = parse_report_summary(content)

    return {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "created_at": parse_report_timestamp(path.name),
        "data_drift_status": summary.get("data_drift_status"),
        "target_drift_status": summary.get("target_drift_status"),
        "concept_drift_status": summary.get("concept_drift_status"),
    }


def parse_report_summary(markdown: str) -> dict[str, str]:
    patterns = {
        "data_drift_status": r"Data drift status: `([^`]+)`",
        "target_drift_status": r"Target drift status: `([^`]+)`",
        "concept_drift_status": r"Concept drift status: `([^`]+)`",
    }

    summary = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, markdown)
        if match:
            summary[key] = match.group(1)

    return summary


def parse_report_timestamp(filename: str) -> str:
    return (
        filename.removeprefix("drift_report_")
        .removesuffix(".md")
        .replace("_", " ")
    )


def resolve_report_path(filename: str) -> Path:
    if not REPORT_FILENAME_RE.match(filename):
        raise HTTPException(status_code=404, detail="Drift report not found")

    report_path = DRIFT_REPORTS_DIR / filename

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Drift report not found")

    return report_path


def parse_evidently_timestamp(filename: str) -> str:
    return (
        filename.removeprefix(REPORT_FILENAME_PREFIX)
        .removesuffix(".html")
        .replace("_", " ")
    )


def list_evidently_report_items() -> list[dict[str, Any]]:
    if not DRIFT_REPORTS_DIR.exists():
        return []

    return [
        {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "created_at": parse_evidently_timestamp(path.name),
        }
        for path in sorted(
            DRIFT_REPORTS_DIR.glob(f"{REPORT_FILENAME_PREFIX}*.html"),
            reverse=True,
        )
        if EVIDENTLY_REPORT_FILENAME_RE.match(path.name)
    ]


def resolve_evidently_report_path(filename: str) -> Path:
    if not EVIDENTLY_REPORT_FILENAME_RE.match(filename):
        raise HTTPException(status_code=404, detail="Drift report not found")

    report_path = DRIFT_REPORTS_DIR / filename

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Drift report not found")

    return report_path


def build_drift_status_snapshot(request: Request) -> dict[str, Any]:
    concept_drift_values = {}

    if request.app.state.feedback_total > 0:
        concept_drift_values = {
            "mismatch_rate": request.app.state.current_concept_drift,
        }

    from defect_detection.api.routes import (  # local import avoids a cycle
        CONCEPT_DRIFT_WARNING_THRESHOLD,
        DATA_DRIFT_WARNING_THRESHOLD,
        TARGET_DRIFT_WARNING_THRESHOLD,
        calculate_drift_status,
    )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "data_drift": {
            "status": calculate_drift_status(
                request.app.state.current_data_drift,
                DATA_DRIFT_WARNING_THRESHOLD,
            ),
            "threshold": DATA_DRIFT_WARNING_THRESHOLD,
            "reference_stats": request.app.state.reference_stats,
            "current_stats": request.app.state.current_image_stats,
            "drift_values": request.app.state.current_data_drift,
        },
        "target_drift": {
            "status": calculate_drift_status(
                request.app.state.current_target_drift,
                TARGET_DRIFT_WARNING_THRESHOLD,
            ),
            "threshold": TARGET_DRIFT_WARNING_THRESHOLD,
            "reference_distribution": (
                request.app.state.reference_target_distribution
            ),
            "current_distribution": (
                request.app.state.current_target_distribution
            ),
            "drift_values": request.app.state.current_target_drift,
        },
        "concept_drift": {
            "status": calculate_drift_status(
                concept_drift_values,
                CONCEPT_DRIFT_WARNING_THRESHOLD,
            ),
            "threshold": CONCEPT_DRIFT_WARNING_THRESHOLD,
            "feedback_total": request.app.state.feedback_total,
            "mismatch_total": request.app.state.feedback_mismatch_total,
            "drift_value": request.app.state.current_concept_drift,
        },
    }
