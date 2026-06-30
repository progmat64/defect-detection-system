import numpy as np
import pytest

from defect_detection.api.storage import (
    connect_database,
    list_recent_prediction_features,
    save_prediction_features,
)
from defect_detection.monitoring.evidently_drift import (
    FEATURE_COLUMNS,
    MIN_CURRENT_SAMPLES,
    build_feature_frame,
    generate_report_file,
    run_drift_report,
    summarize_snapshot,
)


def _records(center: float, count: int, seed: int) -> list[dict[str, float]]:
    rng = np.random.default_rng(seed)
    records = []
    for _ in range(count):
        value = float(abs(rng.normal(center, 0.02)))
        records.append({column: value for column in FEATURE_COLUMNS})
    return records


def test_build_feature_frame_has_expected_columns():
    frame = build_feature_frame(_records(0.3, 3, 0))

    assert list(frame.columns) == list(FEATURE_COLUMNS)
    assert len(frame) == 3


def test_summarize_snapshot_reduces_metrics():
    snapshot = {
        "metrics": [
            {
                "metric_name": "DriftedColumnsCount(drift_share=0.5)",
                "value": {"count": 2.0, "share": 1.0},
            },
            {
                "metric_name": "ValueDrift(column=mean_intensity,method=K-S)",
                "value": 0.0001,
            },
            {
                "metric_name": "ValueDrift(column=std_intensity,method=K-S)",
                "value": 0.8,
            },
        ]
    }

    summary = summarize_snapshot(snapshot)

    assert summary["dataset_drift"] is True
    assert summary["drift_share"] == 1.0
    assert summary["columns"]["mean_intensity"]["drifted"] is True
    assert summary["columns"]["std_intensity"]["drifted"] is False


def test_run_drift_report_detects_shift():
    reference = build_feature_frame(_records(0.30, 200, 1))
    drifted = build_feature_frame(_records(0.60, 60, 2))

    summary = run_drift_report(reference, drifted)

    assert summary["dataset_drift"] is True
    assert summary["drifted_columns"] == len(FEATURE_COLUMNS)


def test_run_drift_report_no_drift_on_same_distribution():
    reference = build_feature_frame(_records(0.30, 200, 1))
    similar = build_feature_frame(_records(0.30, 60, 9))

    summary = run_drift_report(reference, similar)

    assert summary["dataset_drift"] is False


def test_generate_report_file_requires_minimum_samples(tmp_path):
    reference = build_feature_frame(_records(0.30, 50, 1))

    with pytest.raises(ValueError):
        generate_report_file(
            reference,
            _records(0.30, MIN_CURRENT_SAMPLES - 1, 3),
            tmp_path,
        )


def test_generate_report_file_writes_html(tmp_path):
    reference = build_feature_frame(_records(0.30, 100, 1))

    report_path, summary = generate_report_file(
        reference,
        _records(0.60, 20, 2),
        tmp_path,
    )

    assert report_path.exists()
    assert report_path.suffix == ".html"
    assert summary["dataset_drift"] is True


def test_prediction_features_round_trip(tmp_path):
    connection = connect_database(tmp_path / "app.db")
    stats = {column: 0.42 for column in FEATURE_COLUMNS}

    save_prediction_features(
        connection,
        prediction_id="abc",
        created_at="2026-06-30T00:00:00+00:00",
        image_stats=stats,
    )

    rows = list_recent_prediction_features(connection)
    connection.close()

    assert len(rows) == 1
    assert rows[0]["mean_intensity"] == pytest.approx(0.42)
