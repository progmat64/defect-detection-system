import csv
import json
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFECT_CLASS_IDS = (1, 2, 3, 4)
DRIFT_STATUS_NO_DATA = "no_data"
DRIFT_STATUS_OK = "ok"
DRIFT_STATUS_WARNING = "warning"


def calculate_image_stats(image: np.ndarray) -> dict[str, float]:
    normalized = image.astype(np.float32) / 255.0

    channel_means = normalized.mean(axis=(0, 1))
    channel_stds = normalized.std(axis=(0, 1))

    return {
        "mean_intensity": float(normalized.mean()),
        "std_intensity": float(normalized.std()),
        "mean_r": float(channel_means[0]),
        "mean_g": float(channel_means[1]),
        "mean_b": float(channel_means[2]),
        "std_r": float(channel_stds[0]),
        "std_g": float(channel_stds[1]),
        "std_b": float(channel_stds[2]),
    }


def calculate_data_drift(
    current_stats: dict[str, float],
    reference_stats: dict[str, float],
) -> dict[str, float]:
    return {
        stat_name: abs(current_value - reference_stats[stat_name])
        for stat_name, current_value in current_stats.items()
        if stat_name in reference_stats
    }


def calculate_target_distribution(
    class_ids: Iterable[int],
    defect_class_ids: Iterable[int] = DEFECT_CLASS_IDS,
) -> dict[str, float]:
    class_id_keys = [str(class_id) for class_id in defect_class_ids]
    counts = dict.fromkeys(class_id_keys, 0)

    for class_id in class_ids:
        class_id_key = str(class_id)
        if class_id_key in counts:
            counts[class_id_key] += 1

    total = sum(counts.values())

    if total == 0:
        return dict.fromkeys(class_id_keys, 0.0)

    return {class_id: count / total for class_id, count in counts.items()}


def calculate_prediction_target_distribution(
    predictions: list[dict[str, object]],
) -> dict[str, float]:
    predicted_class_ids = [
        int(item["class_id"]) for item in predictions if item["has_defect"]
    ]
    return calculate_target_distribution(predicted_class_ids)


def calculate_target_drift(
    current_distribution: dict[str, float],
    reference_distribution: dict[str, float],
) -> dict[str, float]:
    return {
        class_id: abs(current_value - reference_distribution[class_id])
        for class_id, current_value in current_distribution.items()
        if class_id in reference_distribution
    }


def extract_predicted_classes(
    predictions: list[dict[str, object]],
) -> list[int]:
    return [
        int(item["class_id"]) for item in predictions if item["has_defect"]
    ]


def is_prediction_mismatch(
    predicted_classes: list[int],
    true_classes: list[int],
) -> bool:
    return set(predicted_classes) != set(true_classes)


def calculate_concept_drift_value(
    feedback_total: int,
    mismatch_total: int,
) -> float:
    if feedback_total == 0:
        return 0.0

    return mismatch_total / feedback_total


def calculate_drift_status(
    values: dict[str, float],
    threshold: float,
) -> str:
    if not values:
        return DRIFT_STATUS_NO_DATA

    if any(value > threshold for value in values.values()):
        return DRIFT_STATUS_WARNING

    return DRIFT_STATUS_OK


def calculate_reference_image_stats(image_dir: Path) -> dict[str, float]:
    image_paths = sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_paths:
        raise ValueError(f"No images found in {image_dir}")

    total_stats: dict[str, float] = {}

    for image_path in image_paths:
        image = cv2.imread(str(image_path))

        if image is None:
            raise ValueError(f"Failed to read image: {image_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_stats = calculate_image_stats(image)

        for stat_name, value in image_stats.items():
            total_stats[stat_name] = total_stats.get(stat_name, 0.0) + value

    return {
        stat_name: value / len(image_paths)
        for stat_name, value in total_stats.items()
    }


def calculate_reference_target_distribution(
    train_csv_path: Path,
) -> dict[str, float]:
    with train_csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        class_ids = [int(row["ClassId"]) for row in reader]

    if not class_ids:
        raise ValueError(f"No target labels found in {train_csv_path}")

    return calculate_target_distribution(class_ids)


def save_reference_stats(stats: dict[str, float], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(stats, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_reference_stats(path: Path) -> dict[str, float]:
    return json.loads(path.read_text(encoding="utf-8"))
