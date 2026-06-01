from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=TEMPLATE_DIR)
ui_router = APIRouter()


@ui_router.get("/ui")
def inference_page(request: Request):
    return templates.TemplateResponse(
        request,
        "inference.html",
        {
            "active_page": "inference",
        },
    )


@ui_router.get("/ui/predictions")
def predictions_page(request: Request):
    return templates.TemplateResponse(
        request,
        "predictions.html",
        {
            "active_page": "predictions",
            "predictions": request.app.state.prediction_history,
        },
    )


@ui_router.get("/ui/experiments")
def experiments_page(request: Request):
    return templates.TemplateResponse(
        request,
        "experiments.html",
        {
            "active_page": "experiments",
            "mlflow_url": "http://localhost:5050",
            "model_name": "steel-defect-segmentation",
            "tracking_uri": "http://localhost:5050",
        },
    )
