"""Build the reference image-statistics table used by Evidently drift checks.

Each row holds the per-image statistics of a single reference image. The table
is the baseline distribution that incoming predictions are compared against.

In production the canonical source is ``data/raw/train_images`` (pulled via
DVC). For a runnable demo any image directory works.
"""

import argparse
import csv
from pathlib import Path

import cv2

from defect_detection.monitoring.drift import (
    IMAGE_EXTENSIONS,
    calculate_image_stats,
)
from defect_detection.monitoring.evidently_drift import FEATURE_COLUMNS

DEFAULT_SAMPLE_SIZE = 300


def build_reference_features(
    image_dir: Path,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
) -> list[dict[str, float]]:
    image_paths = sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_paths:
        raise ValueError(f"No images found in {image_dir}")

    if sample_size > 0:
        image_paths = image_paths[:sample_size]

    rows = []
    for image_path in image_paths:
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to read image: {image_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        rows.append(calculate_image_stats(image))

    return rows


def save_reference_features(
    rows: list[dict[str, float]],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(FEATURE_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {column: row[column] for column in FEATURE_COLUMNS}
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Evidently reference feature table."
    )
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("monitoring/reference_features.csv"),
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Max number of images to sample (0 = all).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_reference_features(args.image_dir, args.sample_size)
    save_reference_features(rows, args.output)
    print(f"Wrote {len(rows)} reference rows to {args.output}")


if __name__ == "__main__":
    main()
