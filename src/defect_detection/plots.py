# plots.py
# Visualization utilities

import random

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import torch

from defect_detection.config import CFG, CLASS_COLORS
from defect_detection.features import denormalize


def visualize_predictions(
    model, dataset, n_samples=3, thresholds=None, device=None
):
    """Plot image with ground-truth and predicted masks side-by-side."""
    if device is None:
        from features import get_device

        device = get_device()

    thresholds = thresholds or CFG["PRED_THRESHOLDS"]
    model.eval()
    indices = random.sample(range(len(dataset)), n_samples)
    fig, axes = plt.subplots(n_samples, 2, figsize=(22, 5 * n_samples))

    for row_idx, ds_idx in enumerate(indices):
        image, gt_mask, _ = dataset[ds_idx]
        with torch.no_grad():
            logits = model(image.unsqueeze(0).to(device))
        probs = torch.sigmoid(logits).squeeze(0).cpu()

        img_np = denormalize(image)

        for col_idx, (title_suffix, mask_src) in enumerate(
            [
                ("Ground Truth", gt_mask),
                (
                    "Prediction",
                    torch.stack(
                        [(probs[c] > thresholds[c]).float() for c in range(4)]
                    ),
                ),
            ]
        ):
            ax = axes[row_idx, col_idx]
            ax.imshow(img_np)
            overlay = np.zeros((*img_np.shape[:2], 4), dtype=np.float32)
            for c in range(4):
                m = mask_src[c].numpy().astype(bool)
                if m.any():
                    col = plt.cm.colors.to_rgba(CLASS_COLORS[c], alpha=0.45)
                    overlay[m] = col
            ax.imshow(overlay)
            ax.set_title(
                f"{dataset.df.iloc[ds_idx]['ImageId']} — {title_suffix}",
                fontsize=10,
            )
            ax.axis("off")

    patches = [
        mpatches.Patch(color=c, label=f"Defect {i + 1}")
        for i, c in enumerate(CLASS_COLORS)
    ]
    fig.legend(handles=patches, loc="lower center", ncol=4, fontsize=11)
    plt.tight_layout()
    plt.show()


def plot_defect_distribution(df):
    """Plot defect distribution per class."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 4))

    # Defect count per class
    class_counts = df.groupby("ClassId")["has_defect"].sum()
    bars = axes[0].bar(
        [f"Class {i}" for i in class_counts.index],
        class_counts.values,
        color=CLASS_COLORS,
        edgecolor="black",
        linewidth=0.8,
    )
    for bar, val in zip(bars, class_counts.values, strict=False):
        axes[0].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 30,
            f"{val:,}",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    axes[0].set_title("Defect Count per Class", fontsize=12)
    axes[0].set_ylabel("Number of Images")
    axes[0].set_ylim(0, class_counts.max() * 1.15)
    axes[0].grid(axis="y", alpha=0.3)

    # Defect rate per class (as % of total images)
    total_images = df["ImageId"].nunique()
    defect_rates = class_counts / total_images * 100
    axes[1].bar(
        [f"Class {i}" for i in defect_rates.index],
        defect_rates.values,
        color=CLASS_COLORS,
        edgecolor="black",
        linewidth=0.8,
    )
    for bar, val in zip(axes[1].patches, defect_rates.values, strict=False):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{val:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    axes[1].set_title("Defect Rate per Class (% of all images)", fontsize=12)
    axes[1].set_ylabel("% of Images")
    axes[1].set_ylim(0, defect_rates.max() * 1.15)
    axes[1].grid(axis="y", alpha=0.3)

    plt.suptitle(
        "Class Imbalance — Severstal Steel Defect Dataset",
        fontsize=13,
        fontweight="bold",
    )
    plt.tight_layout()
    plt.show()


def plot_training_curves(history):
    """Plot training and validation loss/dice curves."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(history["train_loss"], label="Train Loss")
    axes[0].plot(history["val_loss"], label="Val Loss")
    axes[0].set_title("Loss (Dice + BCE)")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(history["train_dice"], label="Train Dice")
    axes[1].plot(history["val_dice"], label="Val Dice")
    axes[1].set_title("Dice Score")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.suptitle("Training Curves — Severstal Defect Detection", fontsize=14)
    plt.tight_layout()
    plt.show()
