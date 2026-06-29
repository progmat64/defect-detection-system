import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from defect_detection.monitoring.report import (
    generate_markdown_report,
    save_markdown_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DRIFT_REPORTS_DIR = PROJECT_ROOT / "reports" / "drift"
REPORT_FILENAME_RE = re.compile(
    r"^drift_report_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.md$"
)

drift_reports_router = APIRouter(prefix="/drift/reports")


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
