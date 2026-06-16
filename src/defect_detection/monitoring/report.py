import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen


def load_drift_status_from_url(status_url: str) -> dict[str, object]:
    with urlopen(status_url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def load_drift_status_from_file(status_path: Path) -> dict[str, object]:
    return json.loads(status_path.read_text(encoding="utf-8"))


def generate_markdown_report(status: dict[str, object]) -> str:
    data_drift = status["data_drift"]
    target_drift = status["target_drift"]
    concept_drift = status["concept_drift"]

    return "\n".join(
        [
            "# Drift Report",
            "",
            f"Generated at: `{status['generated_at']}`",
            "",
            "## Summary",
            "",
            f"- Data drift status: `{data_drift['status']}`",
            f"- Target drift status: `{target_drift['status']}`",
            f"- Concept drift status: `{concept_drift['status']}`",
            "",
            "## Data Drift",
            "",
            f"Threshold: `{data_drift['threshold']}`",
            "",
            "Reference image statistics:",
            "",
            _format_mapping(data_drift["reference_stats"]),
            "",
            "Current image statistics:",
            "",
            _format_mapping(data_drift["current_stats"]),
            "",
            "Data drift values:",
            "",
            _format_mapping(data_drift["drift_values"]),
            "",
            "## Target Drift",
            "",
            f"Threshold: `{target_drift['threshold']}`",
            "",
            "Reference target distribution:",
            "",
            _format_mapping(target_drift["reference_distribution"]),
            "",
            "Current predicted target distribution:",
            "",
            _format_mapping(target_drift["current_distribution"]),
            "",
            "Target drift values:",
            "",
            _format_mapping(target_drift["drift_values"]),
            "",
            "## Concept Drift",
            "",
            f"Threshold: `{concept_drift['threshold']}`",
            f"Feedback total: `{concept_drift['feedback_total']}`",
            f"Mismatch total: `{concept_drift['mismatch_total']}`",
            f"Concept drift value: `{concept_drift['drift_value']}`",
            "",
        ]
    )


def save_markdown_report(markdown: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
    report_path = output_dir / f"drift_report_{timestamp}.md"
    report_path.write_text(markdown, encoding="utf-8")
    return report_path


def _format_mapping(mapping: dict[str, object]) -> str:
    if not mapping:
        return "_No data yet._"

    return "\n".join(
        f"- `{key}`: `{value}`" for key, value in sorted(mapping.items())
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a drift report.")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--status-url",
        default="http://127.0.0.1:8000/drift/status",
        help="Drift status API URL.",
    )
    source_group.add_argument(
        "--status-json",
        type=Path,
        help="Local drift status JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/drift"),
        help="Directory where the Markdown report will be saved.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.status_json:
        status = load_drift_status_from_file(args.status_json)
    else:
        status = load_drift_status_from_url(args.status_url)

    report_path = save_markdown_report(
        generate_markdown_report(status),
        args.output_dir,
    )
    print(report_path)


if __name__ == "__main__":
    main()
