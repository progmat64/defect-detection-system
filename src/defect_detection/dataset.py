# dataset.py
# Dataset classes and data loading utilities

import os

import albumentations as A
import cv2
import numpy as np
import pandas as pd
from albumentations.pytorch import ToTensorV2
from config import CFG, IMAGENET_MEAN, IMAGENET_STD
from features import rle_decode
from torch.utils.data import Dataset


def get_train_transforms(h=CFG["IMG_H"], w=CFG["IMG_W"]):
    """Get training data augmentations."""
    return A.Compose(
        [
            A.Resize(h, w),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.ShiftScaleRotate(shift_limit=0.0, scale_limit=0.1, rotate_limit=5, p=0.4),
            A.OneOf(
                [
                    A.RandomBrightnessContrast(
                        brightness_limit=0.2, contrast_limit=0.2
                    ),
                    A.HueSaturationValue(
                        hue_shift_limit=5, sat_shift_limit=20, val_shift_limit=20
                    ),
                ],
                p=0.4,
            ),
            A.OneOf(
                [
                    A.ElasticTransform(alpha=80, sigma=80 * 0.05, p=0.3),
                    A.GridDistortion(num_steps=5, distort_limit=0.2, p=0.3),
                ],
                p=0.25,
            ),
            A.CoarseDropout(
                max_holes=8, max_height=16, max_width=16, fill_value=0, p=0.2
            ),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ]
    )


def get_val_transforms(h=CFG["IMG_H"], w=CFG["IMG_W"]):
    """Get validation transforms (no augmentation, just resize and normalize)."""
    return A.Compose(
        [
            A.Resize(h, w),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ]
    )


class SteelDataset(Dataset):
    """
    Dataset for steel defect detection.

    Returns:
        image      : FloatTensor (3, H, W) — normalised
        mask       : FloatTensor (4, H, W) — one channel per defect class, 0/1
        has_defect : int (0 or 1) — used by WeightedRandomSampler
    """

    def __init__(self, df: pd.DataFrame, image_dir: str, transforms=None):
        self.df = df.reset_index(drop=True)
        self.image_dir = image_dir
        self.transforms = transforms

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = os.path.join(self.image_dir, row["ImageId"])

        image = cv2.imread(img_path)
        if image is None:
            raise FileNotFoundError(f"Image not found: {img_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        h, w = image.shape[:2]
        mask = np.zeros((h, w, 4), dtype=np.uint8)  # (H, W, 4)

        for cls_idx, col in enumerate(["mask_1", "mask_2", "mask_3", "mask_4"]):
            rle = row[col]
            if isinstance(rle, str) and rle.strip():
                mask[:, :, cls_idx] = rle_decode(rle, shape=(h, w))

        if self.transforms:
            aug = self.transforms(image=image, mask=mask)
            image = aug["image"]  # (3, H, W) FloatTensor
            mask = aug["mask"].permute(2, 0, 1).float()  # (4, H, W)

        has_defect = int(mask.sum() > 0)
        return image, mask, has_defect


class TestDataset(Dataset):
    """Dataset for test/inference images."""

    def __init__(self, image_ids, image_dir, transforms):
        self.image_ids = image_ids
        self.image_dir = image_dir
        self.transforms = transforms

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):
        img_id = self.image_ids[idx]
        img_path = os.path.join(self.image_dir, img_id)
        image = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
        orig_h, orig_w = image.shape[:2]
        aug = self.transforms(image=image)
        return aug["image"], img_id, orig_h, orig_w
