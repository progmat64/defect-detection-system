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
- `feature/dvc-gdrive-remote` contains remote DVC storage configuration
- `feature/cookiecutter-structure` contains the Cookiecutter Data Science layout migration

Commits follow the Conventional Commits style, for example:

- `chore: initialize project structure`
- `chore(dvc): track dataset and baseline weights`
- `feat: add unet-resnet34 baseline notebook`
- `refactor: adopt cookiecutter data science structure`

## Project Structure

The repository follows a Cookiecutter Data Science-style layout:

```text
├── data
│   ├── external       <- Data from third-party sources
│   ├── interim        <- Intermediate transformed data
│   ├── processed      <- Final datasets for modeling
│   └── raw            <- Original dataset tracked by DVC
├── docs               <- Project documentation
├── models             <- Trained model artifacts tracked by DVC/MLflow
├── notebooks          <- Exploratory and baseline experiments
├── references         <- Data dictionaries and reference materials
├── reports
│   └── figures        <- Generated reports, drift reports and figures
├── src
│   └── defect_detection
│       ├── config.py
│       ├── dataset.py
│       ├── features.py
│       ├── modeling
│       │   ├── train.py
│       │   └── predict.py
│       └── plots.py
└── tests              <- Automated tests
```

This structure separates exploratory notebooks, reusable production code,
versioned data, model artifacts, generated reports, and automated tests.

## Data Versioning

Large artifacts are tracked with DVC instead of Git:

- dataset metadata is stored in `data/raw.dvc`
- baseline model metadata is stored in `models/best_model.pth.dvc`
- DVC remote storage is configured in `.dvc/config`
- local DVC secrets are stored in `.dvc/config.local` and are not committed

## MLflow Tracking

MLflow is used for experiment tracking and model registration. The training
entrypoint logs baseline parameters, metrics, the model artifact, and registers
the model in MLflow Model Registry as `steel-defect-segmentation`.

Run MLflow locally with Docker Compose:

```bash
docker compose up -d mlflow
```

Open the MLflow UI:

```text
http://localhost:5050
```

Log the baseline model run:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export no_proxy=localhost,127.0.0.1
export NO_PROXY=localhost,127.0.0.1

PYTHONPATH=src MLFLOW_TRACKING_URI=http://127.0.0.1:5050 \
  python -m defect_detection.modeling.train
```

The script creates the `defect-detection-baseline` experiment, logs the
`unet-resnet34-baseline` run, uploads `models/best_model.pth` as an artifact,
and registers model version `steel-defect-segmentation`.

## MLflow on Minikube

The MLflow tracking server can also be deployed to a local Kubernetes cluster
with minikube.

Start minikube and deploy MLflow:

```bash
minikube start
kubectl apply -f k8s/mlflow/
kubectl get pods
kubectl get svc
```

Open the MLflow service:

```bash
minikube service mlflow
```

Use the URL printed by `minikube service mlflow` as the tracking URI:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export no_proxy=localhost,127.0.0.1
export NO_PROXY=localhost,127.0.0.1

PYTHONPATH=src MLFLOW_TRACKING_URI=http://127.0.0.1:<PORT> \
  python -m defect_detection.modeling.train
```

Kubernetes manifests are stored in `k8s/mlflow/`:

- `deployment.yaml` runs the MLflow server
- `service.yaml` exposes MLflow with a NodePort service

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
