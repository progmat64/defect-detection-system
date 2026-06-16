# features.py
# Core functionality: RLE, metrics, loss functions, and model helpers.

import random

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch
import torch.nn as nn
from torch.utils.data import WeightedRandomSampler

from defect_detection.config import CFG, IMAGENET_MEAN, IMAGENET_STD, SEED


def set_seed(seed: int = SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def get_device():
    """Get the available device (CUDA, MPS, or CPU)."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def rle_decode(mask_rle: str, shape=(256, 1600)) -> np.ndarray:
    """Decode RLE string → binary numpy mask. Fortran (column-major) order."""
    if not isinstance(mask_rle, str) or mask_rle.strip() == "":
        return np.zeros(shape, dtype=np.uint8)
    s = mask_rle.split()
    starts = np.asarray(s[0::2], dtype=int) - 1
    lengths = np.asarray(s[1::2], dtype=int)
    img = np.zeros(shape[0] * shape[1], dtype=np.uint8)
    for lo, ln in zip(starts, lengths, strict=False):
        img[lo : lo + ln] = 1
    return img.reshape(shape, order="F")


def rle_encode(mask: np.ndarray) -> str:
    """Encode binary mask → RLE string for submission."""
    pixels = mask.flatten(order="F")
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return " ".join(runs.astype(str))


def dice_score(
    pred: torch.Tensor, target: torch.Tensor, smooth: float = 1e-6
) -> float:
    """
    Compute mean Dice over the batch.
    pred, target: (N, C, H, W) binary tensors
    """
    pred = pred.view(pred.shape[0], pred.shape[1], -1).float()
    target = target.view(target.shape[0], target.shape[1], -1).float()
    intersection = (pred * target).sum(dim=2)
    # When both pred and target are empty for a class → Dice = 1
    dice = torch.where(
        (pred.sum(dim=2) + target.sum(dim=2)) == 0,
        torch.ones_like(intersection),
        (2.0 * intersection + smooth)
        / (pred.sum(dim=2) + target.sum(dim=2) + smooth),
    )
    return dice.mean().item()


class DiceBCELoss(nn.Module):
    """
    Combined Dice + Binary Cross-Entropy loss.
    Dice handles class imbalance (penalises FP/FN equally).
    BCE stabilises gradient flow in early training.
    """

    def __init__(self, bce_weight: float = 0.5, smooth: float = 1.0):
        super().__init__()
        self.bce_weight = bce_weight
        self.smooth = smooth
        self.bce = nn.BCEWithLogitsLoss()

    def dice_loss(
        self, logits: torch.Tensor, targets: torch.Tensor
    ) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        batch_size = probs.shape[0]
        probs = probs.view(batch_size, -1)
        targets = targets.view(batch_size, -1)
        intersection = (probs * targets).sum(dim=1)
        dice = (2.0 * intersection + self.smooth) / (
            probs.sum(dim=1) + targets.sum(dim=1) + self.smooth
        )
        return 1.0 - dice.mean()

    def forward(
        self, logits: torch.Tensor, targets: torch.Tensor
    ) -> torch.Tensor:
        return self.bce_weight * self.bce(logits, targets) + (
            1 - self.bce_weight
        ) * self.dice_loss(logits, targets)


def build_model() -> nn.Module:
    """Build U-Net model with EfficientNet-B4 encoder."""
    model = smp.Unet(
        encoder_name=CFG["ENCODER"],
        encoder_weights=CFG["ENCODER_WEIGHTS"],
        in_channels=3,
        classes=CFG["NUM_CLASSES"],
        activation=None,
    )
    device = get_device()
    model = model.to(device)
    if torch.cuda.device_count() > 1:
        print(f"Using {torch.cuda.device_count()} GPUs")
        model = nn.DataParallel(model)
    return model


def build_weighted_sampler(dataset) -> WeightedRandomSampler:
    """
    Oversamples images that contain defects so the model sees them more often.
    """
    labels = dataset.df["has_any_defect"].values.astype(int)
    class_counts = np.bincount(labels)  # [n_no_defect, n_defect]
    class_weights = 1.0 / class_counts  # inverse frequency
    sample_weights = class_weights[labels]
    sampler = WeightedRandomSampler(
        weights=torch.from_numpy(sample_weights).float(),
        num_samples=len(sample_weights),
        replacement=True,
    )
    return sampler


class EarlyStopping:
    """Early stopping callback."""

    def __init__(self, patience: int, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_score = None

    def step(self, score: float) -> bool:
        """Returns True when training should stop."""
        if self.best_score is None or score > self.best_score + self.min_delta:
            self.best_score = score
            self.counter = 0
        else:
            self.counter += 1
        return self.counter >= self.patience


def post_process_mask(mask: np.ndarray, min_size: int) -> np.ndarray:
    """Remove connected components smaller than min_size pixels."""
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )
    cleaned = np.zeros_like(mask)
    for label_idx in range(1, num_labels):  # 0 = background
        if stats[label_idx, cv2.CC_STAT_AREA] >= min_size:
            cleaned[labels == label_idx] = 1
    return cleaned


def denormalize(tensor: torch.Tensor) -> np.ndarray:
    """Convert normalised (3, H, W) tensor → (H, W, 3) uint8 numpy array."""
    mean = torch.tensor(IMAGENET_MEAN).view(3, 1, 1)
    std = torch.tensor(IMAGENET_STD).view(3, 1, 1)
    img = (tensor.cpu() * std + mean).clamp(0, 1).permute(1, 2, 0).numpy()
    return (img * 255).astype(np.uint8)
