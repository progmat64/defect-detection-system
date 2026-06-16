import argparse
from pathlib import Path

from defect_detection.monitoring.drift import (
    calculate_reference_image_stats,
    save_reference_stats,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build reference image statistics for data drift."
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("data/raw/train_images"),
        help="Directory with reference training images.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("monitoring/reference_stats.json"),
        help="Output JSON file for reference image statistics.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = calculate_reference_image_stats(args.image_dir)
    save_reference_stats(stats, args.output)


if __name__ == "__main__":
    main()
