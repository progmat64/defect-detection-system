import numpy as np
import pytest

from defect_detection.monitoring.drift import (
    calculate_concept_drift_value,
    calculate_data_drift,
    calculate_drift_status,
    calculate_image_stats,
    calculate_prediction_target_distribution,
    calculate_reference_image_stats,
    calculate_reference_target_distribution,
    calculate_target_distribution,
    calculate_target_drift,
    extract_predicted_classes,
    is_prediction_mismatch,
    load_reference_stats,
    save_reference_stats,
)


def test_calculate_image_stats_for_black_image():
    image = np.zeros((10, 20, 3), dtype=np.uint8)

    stats = calculate_image_stats(image)

    assert stats["mean_intensity"] == 0.0
    assert stats["std_intensity"] == 0.0
    assert stats["mean_r"] == 0.0
    assert stats["mean_g"] == 0.0
    assert stats["mean_b"] == 0.0


def test_calculate_image_stats_for_white_image():
    image = np.full((10, 20, 3), 255, dtype=np.uint8)

    stats = calculate_image_stats(image)

    assert stats["mean_intensity"] == 1.0
    assert stats["std_intensity"] == 0.0
    assert stats["mean_r"] == 1.0
    assert stats["mean_g"] == 1.0
    assert stats["mean_b"] == 1.0


def test_calculate_data_drift_against_reference_stats():
    current_stats = {
        "mean_intensity": 0.7,
        "std_intensity": 0.1,
    }
    reference_stats = {
        "mean_intensity": 0.5,
        "std_intensity": 0.25,
    }

    drift = calculate_data_drift(current_stats, reference_stats)

    assert drift["mean_intensity"] == pytest.approx(0.2)
    assert drift["std_intensity"] == pytest.approx(0.15)


def test_calculate_reference_image_stats_from_directory(tmp_path):
    import cv2

    black_image = np.zeros((10, 20, 3), dtype=np.uint8)
    white_image = np.full((10, 20, 3), 255, dtype=np.uint8)

    assert cv2.imwrite(str(tmp_path / "black.jpg"), black_image)
    assert cv2.imwrite(str(tmp_path / "white.jpg"), white_image)

    stats = calculate_reference_image_stats(tmp_path)

    assert stats["mean_intensity"] == pytest.approx(0.5, abs=0.01)
    assert stats["mean_r"] == pytest.approx(0.5, abs=0.01)
    assert stats["mean_g"] == pytest.approx(0.5, abs=0.01)
    assert stats["mean_b"] == pytest.approx(0.5, abs=0.01)


def test_save_and_load_reference_stats(tmp_path):
    output_path = tmp_path / "reference_stats.json"
    stats = {
        "mean_intensity": 0.5,
        "std_intensity": 0.25,
    }

    save_reference_stats(stats, output_path)
    loaded_stats = load_reference_stats(output_path)

    assert loaded_stats == stats


def test_calculate_target_distribution():
    distribution = calculate_target_distribution([1, 1, 3, 4])

    assert distribution["1"] == 0.5
    assert distribution["2"] == 0.0
    assert distribution["3"] == 0.25
    assert distribution["4"] == 0.25


def test_calculate_prediction_target_distribution():
    predictions = [
        {"class_id": 1, "has_defect": True},
        {"class_id": 2, "has_defect": False},
        {"class_id": 3, "has_defect": True},
        {"class_id": 4, "has_defect": True},
    ]

    distribution = calculate_prediction_target_distribution(predictions)

    assert distribution["1"] == pytest.approx(1 / 3)
    assert distribution["2"] == 0.0
    assert distribution["3"] == pytest.approx(1 / 3)
    assert distribution["4"] == pytest.approx(1 / 3)


def test_calculate_target_drift():
    current_distribution = {
        "1": 0.5,
        "2": 0.0,
    }
    reference_distribution = {
        "1": 0.2,
        "2": 0.1,
    }

    drift = calculate_target_drift(current_distribution, reference_distribution)

    assert drift["1"] == pytest.approx(0.3)
    assert drift["2"] == pytest.approx(0.1)


def test_calculate_reference_target_distribution_from_train_csv(tmp_path):
    train_csv = tmp_path / "train.csv"
    train_csv.write_text(
        "ImageId,ClassId,EncodedPixels\n"
        "image_1.jpg,1,1 2\n"
        "image_2.jpg,1,3 4\n"
        "image_3.jpg,3,5 6\n"
        "image_4.jpg,4,7 8\n",
        encoding="utf-8",
    )

    distribution = calculate_reference_target_distribution(train_csv)

    assert distribution["1"] == 0.5
    assert distribution["2"] == 0.0
    assert distribution["3"] == 0.25
    assert distribution["4"] == 0.25


def test_extract_predicted_classes():
    predictions = [
        {"class_id": 1, "has_defect": True},
        {"class_id": 2, "has_defect": False},
        {"class_id": 3, "has_defect": True},
    ]

    assert extract_predicted_classes(predictions) == [1, 3]


def test_is_prediction_mismatch_compares_sets():
    assert is_prediction_mismatch([1, 3], [3, 1]) is False
    assert is_prediction_mismatch([1, 3], [1]) is True


def test_calculate_concept_drift_value():
    assert calculate_concept_drift_value(feedback_total=0, mismatch_total=0) == 0.0
    assert calculate_concept_drift_value(feedback_total=4, mismatch_total=1) == 0.25


def test_calculate_drift_status():
    assert calculate_drift_status({}, threshold=0.2) == "no_data"
    assert calculate_drift_status({"mean": 0.1}, threshold=0.2) == "ok"
    assert calculate_drift_status({"mean": 0.3}, threshold=0.2) == "warning"
