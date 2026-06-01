from pathlib import Path

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch

from defect_detection.config import CFG, IMAGENET_MEAN, IMAGENET_STD
from defect_detection.features import rle_encode


def decode_image(image_bytes: bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid image bytes")

    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def preprocess_image(image: np.ndarray) -> torch.Tensor:
    resized = cv2.resize(image, (CFG["IMG_W"], CFG["IMG_H"]))

    normalized = resized.astype(np.float32) / 255.0
    normalized = (normalized - IMAGENET_MEAN) / IMAGENET_STD

    tensor = torch.from_numpy(normalized).permute(2, 0, 1).float()

    return tensor.unsqueeze(0)


def load_model(checkpoint_path: Path) -> torch.nn.Module:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model_cfg = checkpoint.get("cfg", CFG)

    model = smp.Unet(
        encoder_name=model_cfg["ENCODER"],
        encoder_weights=None,
        in_channels=3,
        classes=model_cfg["NUM_CLASSES"],
        activation=None,
    )

    state_dict = checkpoint["model_state_dict"]

    cleaned_state_dict = {}
    for key, value in state_dict.items():
        cleaned_key = key.removeprefix("module.")
        cleaned_state_dict[cleaned_key] = value

    model.load_state_dict(cleaned_state_dict)
    model.eval()

    return model


def postprocess_output(logits: torch.Tensor) -> list[dict[str, object]]:
    probabilities = torch.sigmoid(logits)
    masks = probabilities[0].detach().cpu().numpy()

    predictions = []

    for class_idx, mask in enumerate(masks):
        threshold = CFG["PRED_THRESHOLDS"][class_idx]
        binary_mask = (mask > threshold).astype(np.uint8)

        area_pixels = int(binary_mask.sum())
        rle = rle_encode(binary_mask) if area_pixels > 0 else ""

        predictions.append(
            {
                "class_id": class_idx + 1,
                "has_defect": area_pixels > 0,
                "area_pixels": area_pixels,
                "rle": rle,
            }
        )

    return predictions


def predict_image(model: torch.nn.Module, image_bytes: bytes) -> dict[str, object]:
    image = decode_image(image_bytes)
    tensor = preprocess_image(image)

    with torch.no_grad():
        logits = model(tensor)

    predictions = postprocess_output(logits)

    return {
        "image_height": image.shape[0],
        "image_width": image.shape[1],
        "image_channels": image.shape[2],
        "tensor_shape": list(tensor.shape),
        "predictions": predictions,
    }
