from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from defect_detection.api.drift_reports import (
    DRIFT_REPORTS_DIR,
    build_drift_status_snapshot,
    generate_markdown_report,
    list_drift_report_items,
    list_evidently_report_items,
    resolve_report_path,
    save_markdown_report,
)
from defect_detection.api.storage import (
    list_predictions,
    list_recent_prediction_features,
)
from defect_detection.api.translations import (
    build_language_urls,
    build_page_urls,
    get_translations,
)
from defect_detection.monitoring.evidently_drift import (
    MIN_CURRENT_SAMPLES,
    generate_report_file,
)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=TEMPLATE_DIR)
ui_router = APIRouter()


def template_context(request: Request, active_page: str) -> dict[str, object]:
    language, translations = get_translations(request.query_params.get("lang"))

    return {
        "active_page": active_page,
        "lang": language,
        "language_urls": build_language_urls(active_page),
        "page_urls": build_page_urls(language),
        "t": translations,
    }


@ui_router.get("/ui")
def inference_page(request: Request):
    return templates.TemplateResponse(
        request,
        "inference.html",
        template_context(request, "inference"),
    )


@ui_router.get("/ui/predictions")
def predictions_page(request: Request):
    context = template_context(request, "predictions")
    context["predictions"] = list_predictions(request.app.state.db)

    return templates.TemplateResponse(
        request,
        "predictions.html",
        context,
    )


@ui_router.get("/ui/drift-reports")
def drift_reports_page(request: Request):
    context = template_context(request, "drift_reports")
    selected_filename = request.query_params.get("report")
    evidently_status = request.query_params.get("evidently_status")
    selected_report = None

    if selected_filename:
        report_path = resolve_report_path(selected_filename)
        selected_report = {
            "filename": report_path.name,
            "content": report_path.read_text(encoding="utf-8"),
        }

    context.update(
        {
            "reports": list_drift_report_items(),
            "evidently_reports": list_evidently_report_items(),
            "evidently_status": evidently_status,
            "min_evidently_samples": MIN_CURRENT_SAMPLES,
            "selected_report": selected_report,
        }
    )

    return templates.TemplateResponse(
        request,
        "drift_reports.html",
        context,
    )


@ui_router.post("/ui/drift-reports/generate")
def generate_drift_report_page(request: Request):
    report_path = save_markdown_report(
        generate_markdown_report(build_drift_status_snapshot(request)),
        DRIFT_REPORTS_DIR,
    )
    language = request.query_params.get("lang", "ru")

    return RedirectResponse(
        url=f"/ui/drift-reports?lang={language}&report={report_path.name}",
        status_code=303,
    )


@ui_router.post("/ui/drift-reports/evidently/generate")
def generate_evidently_report_page(request: Request):
    language = request.query_params.get("lang", "ru")
    reference_frame = getattr(request.app.state, "reference_features", None)

    if reference_frame is None:
        return RedirectResponse(
            url=(
                f"/ui/drift-reports?lang={language}"
                "&evidently_status=missing_reference"
            ),
            status_code=303,
        )

    current_records = list_recent_prediction_features(request.app.state.db)

    try:
        generate_report_file(
            reference_frame,
            current_records,
            DRIFT_REPORTS_DIR,
        )
    except ValueError:
        return RedirectResponse(
            url=(
                f"/ui/drift-reports?lang={language}"
                f"&evidently_status=not_enough_samples"
            ),
            status_code=303,
        )

    return RedirectResponse(
        url=f"/ui/drift-reports?lang={language}&evidently_status=created",
        status_code=303,
    )


@ui_router.get("/ui/experiments")
def experiments_page(request: Request):
    context = template_context(request, "experiments")
    context.update(
        {
            "mlflow_url": "http://localhost:5050",
            "model_name": "steel-defect-segmentation",
            "model_path": getattr(request.app.state, "model_path", "-"),
            "model_version": getattr(
                request.app.state,
                "model_version",
                "-",
            ),
            "tracking_uri": "http://localhost:5050",
        }
    )

    return templates.TemplateResponse(
        request,
        "experiments.html",
        context,
    )
