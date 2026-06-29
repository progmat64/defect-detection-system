from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from defect_detection.api.drift_reports import drift_reports_router
from defect_detection.api.metrics import MODEL_INFO
from defect_detection.api.middleware import prometheus_middleware
from defect_detection.api.routes import router
from defect_detection.api.storage import connect_database, get_feedback_totals
from defect_detection.api.ui import ui_router
from defect_detection.modeling.predict import load_model
from defect_detection.monitoring.drift import load_reference_stats

PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pth"
REFERENCE_STATS_PATH = PROJECT_ROOT / "monitoring" / "reference_stats.json"
REFERENCE_TARGET_DISTRIBUTION_PATH = (
    PROJECT_ROOT / "monitoring" / "reference_target_distribution.json"
)
STATIC_DIR = API_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model(MODEL_PATH)
    app.state.model_path = str(MODEL_PATH)
    app.state.model_version = "local-baseline"
    MODEL_INFO.labels(
        version=app.state.model_version,
        path=app.state.model_path,
    ).set(1)
    app.state.reference_stats = load_reference_stats(REFERENCE_STATS_PATH)
    app.state.reference_target_distribution = load_reference_stats(
        REFERENCE_TARGET_DISTRIBUTION_PATH
    )
    app.state.db = connect_database(PROJECT_ROOT / "storage" / "app.db")
    feedback_total, mismatch_total = get_feedback_totals(app.state.db)
    app.state.feedback_total = feedback_total
    app.state.feedback_mismatch_total = mismatch_total
    app.state.current_image_stats = {}
    app.state.current_data_drift = {}
    app.state.current_target_distribution = {}
    app.state.current_target_drift = {}
    app.state.current_concept_drift = 0.0
    try:
        yield
    finally:
        app.state.db.close()


app = FastAPI(title="Defect Detection API", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.middleware("http")(prometheus_middleware)
app.include_router(router)
app.include_router(drift_reports_router)
app.include_router(ui_router)
