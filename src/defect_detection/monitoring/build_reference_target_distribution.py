import argparse
from pathlib import Path

from defect_detection.monitoring.drift import (
    calculate_reference_target_distribution,
    save_reference_stats,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build reference target distribution for target drift monitoring."
    )
    parser.add_argument(
        "--train-csv",
        type=Path,
        default=Path("data/raw/train.csv"),
        help="Training CSV with ClassId labels.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("monitoring/reference_target_distribution.json"),
        help="Output JSON file for reference target distribution.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    distribution = calculate_reference_target_distribution(args.train_csv)
    save_reference_stats(distribution, args.output)


if __name__ == "__main__":
    main()
