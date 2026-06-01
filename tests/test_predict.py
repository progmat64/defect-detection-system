import cv2
import numpy as np
import pytest

from defect_detection.config import CFG
from defect_detection.modeling.predict import decode_image, preprocess_image


def test_decode_image_from_png_bytes():
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)

    assert success

    decoded = decode_image(encoded.tobytes())

    assert decoded.shape == (10, 20, 3)


def test_decode_image_rejects_invalid_bytes():
    with pytest.raises(ValueError, match="Invalid image bytes"):
        decode_image(b"not an image")


def test_preprocess_image_returns_model_tensor():
    image = np.zeros((10, 20, 3), dtype=np.uint8)

    tensor = preprocess_image(image)

    assert tensor.shape == (1, 3, CFG["IMG_H"], CFG["IMG_W"])
    assert str(tensor.dtype) == "torch.float32"
