# config.py
# Configuration parameters for the defect detection system

# ImageNet normalization constants
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Class colors for visualization
CLASS_COLORS = ["red", "blue", "green", "orange"]

# Configuration dictionary
CFG = dict(
    # Paths
    TRAIN_CSV="../data/raw/train.csv",
    TRAIN_IMGS="../data/raw/train_images",
    TEST_IMGS="../data/raw/test_images",
    SAMPLE_SUB="../data/raw/sample_submission.csv",
    # Image geometry — keep native width to preserve thin horizontal defects
    IMG_H=256,
    IMG_W=1600,
    # Training hyperparameters
    EPOCHS=50,
    BATCH_SIZE=4,
    LR=3e-4,
    WEIGHT_DECAY=1e-4,
    VAL_SPLIT=0.15,
    NUM_WORKERS=0,
    AMP=True,
    PATIENCE=8,
    # Model
    ENCODER="efficientnet-b4",
    ENCODER_WEIGHTS="imagenet",
    NUM_CLASSES=4,
    # Post-processing thresholds — tuned on validation set
    PRED_THRESHOLDS=[0.5, 0.5, 0.5, 0.5],
    MIN_MASK_SIZES=[300, 300, 300, 300],
)

# Random seed for reproducibility
SEED = 42
