from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from defect_detection.api.storage import list_predictions
from defect_detection.api.translations import (
    build_language_urls,
    build_page_urls,
    get_translations,
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
