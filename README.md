# Defect Detection System

Baseline project for steel surface defect segmentation.

## Dataset

The project uses the Severstal Steel Defect Detection dataset structure:

- `data/raw/train.csv` contains run-length encoded masks
- `data/raw/train_images/` contains training images
- `data/raw/test_images/` contains test images
- each image may contain up to 4 defect classes

## Baseline Model

The baseline experiment is a multi-label segmentation setup:

- architecture: U-Net
- encoder: ResNet34
- pretrained weights: ImageNet
- output channels: 4 defect classes
- training workflow: notebook-based experiment in `notebooks/defect-detection.ipynb`

## Repository Workflow

The repository follows a lightweight GitHub Flow:

- `main` stores the stable state
- `feature/project-setup` contains repository setup changes
- `feature/dvc-setup` contains data and model versioning with DVC
- `feature/baseline-model` contains the baseline experiment

Commits follow the Conventional Commits style, for example:

- `chore: initialize project structure`
- `chore(dvc): track dataset and baseline weights`
- `feat: add unet-resnet34 baseline notebook`

## Data Versioning

Large artifacts are tracked with DVC instead of Git:

- dataset metadata is stored in `data/raw.dvc`
- baseline model metadata is stored in `models/best_model.pth.dvc`
- the local DVC remote is configured outside the repository

## Dependencies

The baseline notebook relies on:

- `torch`
- `segmentation-models-pytorch`
- `albumentations`
- `opencv-python`
- `pandas`
- `matplotlib`
- `scikit-learn`
- `iterative-stratification`
- `tqdm`
