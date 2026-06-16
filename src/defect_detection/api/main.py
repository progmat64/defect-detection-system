from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from defect_detection.api.middleware import prometheus_middleware
from defect_detection.api.routes import router
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
    app.state.reference_stats = load_reference_stats(REFERENCE_STATS_PATH)
    app.state.reference_target_distribution = load_reference_stats(
        REFERENCE_TARGET_DISTRIBUTION_PATH
    )
    app.state.predictions = {}
    app.state.feedback_total = 0
    app.state.feedback_mismatch_total = 0
    app.state.prediction_history = []
    app.state.retraining_jobs = {}
    app.state.current_image_stats = {}
    app.state.current_data_drift = {}
    app.state.current_target_distribution = {}
    app.state.current_target_drift = {}
    app.state.current_concept_drift = 0.0
    yield


app = FastAPI(title="Defect Detection API", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.middleware("http")(prometheus_middleware)
app.include_router(router)
app.include_router(ui_router)
