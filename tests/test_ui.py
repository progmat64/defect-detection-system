from contextlib import asynccontextmanager

import torch
from fastapi.testclient import TestClient

from defect_detection.api.main import app


class FakeModel:
    def __call__(self, tensor):
        return torch.zeros((1, 4, tensor.shape[2], tensor.shape[3]))


@asynccontextmanager
async def _test_lifespan(app):
    app.state.model = FakeModel()
    app.state.reference_stats = {}
    app.state.reference_target_distribution = {}
    app.state.predictions = {}
    app.state.feedback_total = 0
    app.state.feedback_mismatch_total = 0
    app.state.prediction_history = [
        {
            "prediction_id": "prediction-1",
            "created_at": "2026-06-01T12:00:00+00:00",
            "filename": "test.png",
            "content_type": "image/png",
            "size_bytes": 128,
            "image_preview": "data:image/png;base64,",
            "predicted_classes": [1, 3],
            "has_any_defect": True,
        }
    ]
    app.state.current_image_stats = {}
    app.state.current_data_drift = {}
    app.state.current_target_distribution = {}
    app.state.current_target_drift = {}
    app.state.current_concept_drift = 0.0
    yield


def test_ui_pages_render():
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _test_lifespan

    try:
        with TestClient(app) as client:
            inference_response = client.get("/ui")
            predictions_response = client.get("/ui/predictions")
            experiments_response = client.get("/ui/experiments")
    finally:
        app.router.lifespan_context = original_lifespan

    assert inference_response.status_code == 200
    assert "Inference" in inference_response.text

    assert predictions_response.status_code == 200
    assert "prediction-1" in predictions_response.text

    assert experiments_response.status_code == 200
    assert "steel-defect-segmentation" in experiments_response.text
