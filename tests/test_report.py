from defect_detection.monitoring.report import generate_markdown_report


def test_generate_markdown_report():
    status = {
        "generated_at": "2026-06-01T12:00:00+00:00",
        "data_drift": {
            "status": "warning",
            "threshold": 0.2,
            "reference_stats": {"mean_intensity": 0.5},
            "current_stats": {"mean_intensity": 0.8},
            "drift_values": {"mean_intensity": 0.3},
        },
        "target_drift": {
            "status": "ok",
            "threshold": 0.2,
            "reference_distribution": {"1": 0.5},
            "current_distribution": {"1": 0.4},
            "drift_values": {"1": 0.1},
        },
        "concept_drift": {
            "status": "ok",
            "threshold": 0.2,
            "feedback_total": 4,
            "mismatch_total": 1,
            "drift_value": 0.25,
        },
    }

    report = generate_markdown_report(status)

    assert "# Drift Report" in report
    assert "Data drift status: `warning`" in report
    assert "`mean_intensity`: `0.3`" in report
    assert "Concept drift value: `0.25`" in report
