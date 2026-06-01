from contextlib import asynccontextmanager

import cv2
import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

from defect_detection.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module", autouse=True)
def mock_model_loading():
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _test_lifespan
    yield
    app.router.lifespan_context = original_lifespan


class FakeModel:
    def __call__(self, tensor):
        return torch.zeros((1, 4, tensor.shape[2], tensor.shape[3]))


@asynccontextmanager
async def _test_lifespan(app):
    app.state.model = FakeModel()
    app.state.reference_stats = {
        "mean_intensity": 0.5,
        "std_intensity": 0.25,
        "mean_r": 0.5,
        "mean_g": 0.5,
        "mean_b": 0.5,
        "std_r": 0.25,
        "std_g": 0.25,
        "std_b": 0.25,
    }
    app.state.reference_target_distribution = {
        "1": 0.2,
        "2": 0.1,
        "3": 0.5,
        "4": 0.2,
    }
    app.state.predictions = {}
    app.state.feedback_total = 0
    app.state.feedback_mismatch_total = 0
    app.state.current_image_stats = {}
    app.state.current_data_drift = {}
    app.state.current_target_distribution = {}
    app.state.current_target_drift = {}
    app.state.current_concept_drift = 0.0
    yield


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"model_loaded": True}


def test_predict_rejects_text_file(client):
    response = client.post(
        "/predict",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file type: text/plain"


def test_predict_accepts_png_file(client):
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    response = client.post(
        "/predict",
        files={"file": ("test.png", encoded.tobytes(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["filename"] == "test.png"
    assert payload["content_type"] == "image/png"
    assert payload["size_bytes"] == len(encoded.tobytes())
    assert isinstance(payload["prediction_id"], str)
    assert payload["image_height"] == 10
    assert payload["image_width"] == 20
    assert payload["image_channels"] == 3
    assert payload["tensor_shape"] == [1, 3, 256, 1600]


def test_predict_rejects_invalid_image_bytes(client):
    response = client.post(
        "/predict",
        files={"file": ("test.png", b"not an image", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image bytes"


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "defect_api_requests_total" in response.text
    assert "defect_api_request_latency_seconds" in response.text


def test_predict_records_prediction_metrics(client):
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    client.post(
        "/predict",
        files={"file": ("test.png", encoded.tobytes(), "image/png")},
    )

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "defect_predictions_total" in response.text


def test_predict_records_image_stat_metrics(client):
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    client.post(
        "/predict",
        files={"file": ("test.png", encoded.tobytes(), "image/png")},
    )

    response = client.get("/metrics")

    assert response.status_code == 200
    assert 'defect_image_stat_value{stat_name="mean_intensity"}' in response.text


def test_predict_records_data_drift_metrics(client):
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    client.post(
        "/predict",
        files={"file": ("test.png", encoded.tobytes(), "image/png")},
    )

    response = client.get("/metrics")

    assert response.status_code == 200
    assert 'defect_data_drift_value{stat_name="mean_intensity"}' in response.text


def test_predict_records_target_drift_metrics(client):
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    client.post(
        "/predict",
        files={"file": ("test.png", encoded.tobytes(), "image/png")},
    )

    response = client.get("/metrics")

    assert response.status_code == 200
    assert 'defect_predicted_class_distribution_value{class_id="1"}' in response.text
    assert 'defect_target_drift_value{class_id="1"}' in response.text


def test_feedback_accepts_true_classes_for_existing_prediction(client):
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    predict_response = client.post(
        "/predict",
        files={"file": ("test.png", encoded.tobytes(), "image/png")},
    )
    prediction_id = predict_response.json()["prediction_id"]

    response = client.post(
        "/feedback",
        json={
            "prediction_id": prediction_id,
            "true_classes": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["prediction_id"] == prediction_id
    assert payload["predicted_classes"] == []
    assert payload["true_classes"] == []
    assert payload["is_mismatch"] is False
    assert payload["concept_drift_value"] >= 0.0


def test_feedback_records_concept_drift_metrics(client):
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    predict_response = client.post(
        "/predict",
        files={"file": ("test.png", encoded.tobytes(), "image/png")},
    )
    prediction_id = predict_response.json()["prediction_id"]

    client.post(
        "/feedback",
        json={
            "prediction_id": prediction_id,
            "true_classes": [1],
        },
    )

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "defect_feedback_total" in response.text
    assert "defect_prediction_mismatch_total" in response.text
    assert "defect_concept_drift_value" in response.text


def test_feedback_rejects_unknown_prediction_id(client):
    response = client.post(
        "/feedback",
        json={
            "prediction_id": "missing",
            "true_classes": [],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Prediction not found"


def test_feedback_rejects_invalid_true_class(client):
    response = client.post(
        "/feedback",
        json={
            "prediction_id": "missing",
            "true_classes": [9],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid defect classes: [9]"


def test_drift_status_returns_current_drift_snapshot(client):
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    predict_response = client.post(
        "/predict",
        files={"file": ("test.png", encoded.tobytes(), "image/png")},
    )
    prediction_id = predict_response.json()["prediction_id"]
    client.post(
        "/feedback",
        json={
            "prediction_id": prediction_id,
            "true_classes": [1],
        },
    )

    response = client.get("/drift/status")

    assert response.status_code == 200
    payload = response.json()

    assert "generated_at" in payload
    assert payload["data_drift"]["status"] in {"ok", "warning"}
    assert payload["target_drift"]["status"] in {"ok", "warning"}
    assert payload["concept_drift"]["status"] in {"ok", "warning"}
    assert "mean_intensity" in payload["data_drift"]["drift_values"]
    assert "1" in payload["target_drift"]["drift_values"]
    assert payload["concept_drift"]["feedback_total"] >= 1
