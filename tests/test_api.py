import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from defect_detection.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


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
