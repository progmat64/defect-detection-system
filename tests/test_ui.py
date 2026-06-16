from contextlib import asynccontextmanager

import torch
from fastapi.testclient import TestClient

from defect_detection.api.main import app
from defect_detection.api.storage import connect_database, save_prediction


class FakeModel:
    def __call__(self, tensor):
        return torch.zeros((1, 4, tensor.shape[2], tensor.shape[3]))


@asynccontextmanager
async def _test_lifespan(app):
    app.state.model = FakeModel()
    app.state.reference_stats = {}
    app.state.reference_target_distribution = {}
    app.state.feedback_total = 0
    app.state.feedback_mismatch_total = 0
    app.state.db = connect_database(_test_lifespan.database_path)
    save_prediction(
        app.state.db,
        {
            "prediction_id": "prediction-1",
            "created_at": "2026-06-01T12:00:00+00:00",
            "filename": "test.png",
            "content_type": "image/png",
            "size_bytes": 128,
            "image_preview": "data:image/png;base64,",
            "predicted_classes": [1, 3],
            "has_any_defect": True,
        },
    )
    app.state.current_image_stats = {}
    app.state.current_data_drift = {}
    app.state.current_target_distribution = {}
    app.state.current_target_drift = {}
    app.state.current_concept_drift = 0.0
    try:
        yield
    finally:
        app.state.db.close()


_test_lifespan.database_path = None


def test_ui_pages_render(tmp_path):
    original_lifespan = app.router.lifespan_context
    _test_lifespan.database_path = tmp_path / "ui.db"
    app.router.lifespan_context = _test_lifespan

    try:
        with TestClient(app) as client:
            inference_response = client.get("/ui")
            english_inference_response = client.get("/ui?lang=en")
            predictions_response = client.get("/ui/predictions")
            experiments_response = client.get("/ui/experiments")
    finally:
        app.router.lifespan_context = original_lifespan

    assert inference_response.status_code == 200
    assert 'html lang="ru"' in inference_response.text
    assert "Инференс" in inference_response.text
    assert "Запустить переобучение" in inference_response.text

    assert english_inference_response.status_code == 200
    assert 'html lang="en"' in english_inference_response.text
    assert "Inference" in english_inference_response.text
    assert "Run retraining" in english_inference_response.text

    assert predictions_response.status_code == 200
    assert "prediction-1" in predictions_response.text
    assert "Предсказания" in predictions_response.text

    assert experiments_response.status_code == 200
    assert "steel-defect-segmentation" in experiments_response.text
    assert "Эксперименты" in experiments_response.text
