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

## FastAPI Inference Service

The project includes a FastAPI service for model inference. The service exposes
OpenAPI documentation, health checks, readiness checks, and image prediction.

Available endpoints:

- `/docs` - Swagger UI with OpenAPI documentation
- `/health` - process health check
- `/ready` - model readiness check
- `/predict` - image upload endpoint for defect prediction
- `/predictions` - latest prediction history as JSON
- `/feedback` - operator feedback endpoint for concept drift monitoring
- `/retrain` - retraining trigger endpoint
- `/drift/status` - current drift snapshot for reports and dashboards

Run the API locally from the repository root:

```bash
PYTHONPATH=src uvicorn defect_detection.api.main:app --reload
```

Open the Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Build and run the Docker image:

```bash
docker build -t defect-detection-api:local .
docker run --rm -p 8000:8000 defect-detection-api:local
```

Run with Docker Compose for local debugging:

```bash
docker compose up --build api
```

Run the API together with MLflow:

```bash
docker compose up --build
```

Deploy the API to minikube:

```bash
minikube start
eval $(minikube docker-env)
docker build -t defect-detection-api:local .
kubectl apply -f k8s/api/
kubectl get pods
kubectl get svc
minikube service defect-detection-api
eval $(minikube docker-env -u)
```

The API loads `models/best_model.pth` during FastAPI startup and returns
predictions as four class-level records with defect flags, mask area, and RLE
mask strings. Each prediction response also includes a `prediction_id`, which
can later be used to submit ground-truth feedback.

## Web UI

The project includes a lightweight FastAPI-rendered web interface for production
operations workflows.

Run the API locally:

```bash
PYTHONPATH=src uvicorn defect_detection.api.main:app --reload
```

Open the UI pages:

```text
Inference:    http://127.0.0.1:8000/ui
Predictions:  http://127.0.0.1:8000/ui/predictions
Experiments:  http://127.0.0.1:8000/ui/experiments
```

The UI supports image inference, selected image preview, predicted mask overlay,
class result cards, latest prediction history with thumbnails, drift status
flags, drift warning notifications, an MLflow experiments entry point, and a
retraining trigger button.

## Monitoring and Drift

The API exposes Prometheus metrics at `/metrics`. Docker Compose can run the API,
Prometheus, and Grafana together for local debugging:

```bash
docker compose up --build api prometheus grafana
```

Open the monitoring tools:

```text
Prometheus: http://127.0.0.1:9090
Grafana:    http://127.0.0.1:3000
```

Grafana local credentials:

```text
admin / admin
```

Reference image statistics for data drift are stored in:

```text
monitoring/reference_stats.json
```

Reference class distribution for target drift is stored in:

```text
monitoring/reference_target_distribution.json
```

Rebuild the reference baseline from the training images:

```bash
PYTHONPATH=src python -m defect_detection.monitoring.build_reference_stats \
  --image-dir data/raw/train_images \
  --output monitoring/reference_stats.json
```

Rebuild the reference target distribution from training labels:

```bash
PYTHONPATH=src python -m defect_detection.monitoring.build_reference_target_distribution \
  --train-csv data/raw/train.csv \
  --output monitoring/reference_target_distribution.json
```

Submit feedback for concept drift monitoring:

```json
{
  "prediction_id": "<prediction_id from /predict>",
  "true_classes": [1, 3]
}
```

Concept drift is tracked as the current mismatch rate between predicted defect
classes and feedback true classes.

Generate a Markdown drift report from the running API:

```bash
PYTHONPATH=src python -m defect_detection.monitoring.report \
  --status-url http://127.0.0.1:8000/drift/status \
  --output-dir reports/drift
```

Reports are saved as timestamped Markdown files in:

```text
reports/drift/
```

Useful Prometheus queries:

```promql
defect_api_requests_total
defect_predictions_total
defect_image_stat_value
defect_data_drift_value
defect_predicted_class_distribution_value
defect_target_drift_value
defect_feedback_total
defect_prediction_mismatch_total
defect_concept_drift_value
```

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
