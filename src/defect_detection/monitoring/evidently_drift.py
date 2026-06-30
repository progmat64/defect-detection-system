"""Evidently-backed data drift detection over image statistics.

The lightweight per-request drift in :mod:`defect_detection.monitoring.drift`
feeds the live Prometheus gauges. This module adds a statistically grounded
data drift check (Kolmogorov-Smirnov tests via Evidently) over a *window* of
image-statistic rows: a reference table built from the training images versus
the most recent predictions served by the API.
"""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

FEATURE_COLUMNS = (
    "mean_intensity",
    "std_intensity",
    "mean_r",
    "mean_g",
    "mean_b",
    "std_r",
    "std_g",
    "std_b",
)
DRIFT_SHARE_THRESHOLD = 0.5
MIN_CURRENT_SAMPLES = 5
REPORT_FILENAME_PREFIX = "evidently_report_"


def build_feature_frame(
    records: list[dict[str, float]],
) -> pd.DataFrame:
    """Build a DataFrame with one row of image statistics per record."""
    return pd.DataFrame(
        [
            {column: float(record[column]) for column in FEATURE_COLUMNS}
            for record in records
        ],
        columns=list(FEATURE_COLUMNS),
    )


def _build_dataset(frame: pd.DataFrame) -> Dataset:
    data_definition = DataDefinition(
        numerical_columns=list(FEATURE_COLUMNS),
    )
    return Dataset.from_pandas(frame, data_definition=data_definition)


def run_drift_report(
    reference_frame: pd.DataFrame,
    current_frame: pd.DataFrame,
    html_output_path: Path | None = None,
) -> dict[str, object]:
    """Run the Evidently data drift report and return a compact summary.

    When ``html_output_path`` is provided, the full interactive HTML report is
    saved there as well.
    """
    report = Report([DataDriftPreset(drift_share=DRIFT_SHARE_THRESHOLD)])
    snapshot = report.run(
        reference_data=_build_dataset(reference_frame),
        current_data=_build_dataset(current_frame),
    )

    if html_output_path is not None:
        html_output_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot.save_html(str(html_output_path))

    return summarize_snapshot(snapshot.dict())


def summarize_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    """Reduce a raw Evidently snapshot to a compact, serialisable summary."""
    columns: dict[str, dict[str, object]] = {}
    drift_share = 0.0
    drifted_columns = 0

    for metric in snapshot.get("metrics", []):
        name = str(metric.get("metric_name", ""))
        value = metric.get("value")

        if name.startswith("DriftedColumnsCount") and isinstance(value, dict):
            drifted_columns = int(value.get("count", 0))
            drift_share = float(value.get("share", 0.0))
        elif name.startswith("ValueDrift") and isinstance(value, (int, float)):
            column_name = _extract_column(name)
            p_value = float(value)
            columns[column_name] = {
                "p_value": p_value,
                "drifted": p_value < 0.05,
            }

    return {
        "dataset_drift": drift_share >= DRIFT_SHARE_THRESHOLD,
        "drift_share": drift_share,
        "drifted_columns": drifted_columns,
        "total_columns": len(columns),
        "columns": columns,
    }


def load_reference_features(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    return frame[list(FEATURE_COLUMNS)]


def generate_report_file(
    reference_frame: pd.DataFrame,
    current_records: list[dict[str, float]],
    output_dir: Path,
) -> tuple[Path, dict[str, object]]:
    """Build the current frame, run the report, and persist the HTML file.

    Returns the saved report path and its compact summary.
    """
    if len(current_records) < MIN_CURRENT_SAMPLES:
        raise ValueError(
            "Not enough predictions for an Evidently report: "
            f"need at least {MIN_CURRENT_SAMPLES}, got {len(current_records)}."
        )

    current_frame = build_feature_frame(current_records)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
    report_path = output_dir / f"{REPORT_FILENAME_PREFIX}{timestamp}.html"
    summary = run_drift_report(reference_frame, current_frame, report_path)

    return report_path, summary


def _extract_column(metric_name: str) -> str:
    marker = "column="
    start = metric_name.find(marker)
    if start == -1:
        return metric_name
    start += len(marker)
    end = metric_name.find(",", start)
    if end == -1:
        end = metric_name.find(")", start)
    return metric_name[start:end] if end != -1 else metric_name[start:]
