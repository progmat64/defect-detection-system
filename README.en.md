# Defect Detection System

Russian version: [README.md](README.md).

Reproducible MLOps system for steel surface defect segmentation. The project
covers the production ML lifecycle: data and model versioning, experiment
tracking, FastAPI inference service, Docker/Kubernetes deployment, drift
monitoring, drift reports, Web UI, and GitOps delivery with Argo CD.

## What Is Included

- Dataset: Severstal Steel Defect Detection
- Model: U-Net segmentation model for 4 defect classes
- Project structure: Cookiecutter Data Science-style layout
- Versioning: GitHub Flow, Conventional Commits, DVC for data/model artifacts
- Experiment tracking: MLflow Tracking and Model Registry
- API: FastAPI with OpenAPI, health/readiness checks, image inference
- Runtime storage: SQLite for prediction history, feedback, retraining jobs
- Packaging: Docker image and Docker Compose for local debugging
- Kubernetes: API and MLflow manifests for Minikube
- Monitoring: Prometheus metrics and Grafana dashboards
- Drift: data drift, target drift, concept drift
- Reports: Markdown drift report generation
- Web UI: inference page, prediction history, drift alerts, experiments page
- CD: Argo CD Application for GitOps deployment to Minikube

## Repository Structure

```text
├── data
│   ├── external
│   ├── interim
│   ├── processed
│   └── raw                         <- DVC-tracked dataset
├── k8s
│   ├── api                         <- FastAPI Kubernetes manifests
│   ├── argocd                      <- Argo CD Application manifest
│   └── mlflow                      <- MLflow Kubernetes manifests
├── models                          <- DVC-tracked model artifacts
├── monitoring
│   ├── grafana                     <- Grafana provisioning and dashboards
│   ├── prometheus.yml
│   ├── reference_stats.json
│   └── reference_target_distribution.json
├── notebooks                       <- baseline experiments
├── reports
│   ├── drift                       <- generated drift reports
│   └── figures
├── src/defect_detection
│   ├── api                         <- FastAPI app, UI, metrics
│   ├── modeling                    <- training and inference code
│   ├── monitoring                  <- drift and report utilities
│   ├── config.py
│   ├── dataset.py
│   ├── features.py
│   └── plots.py
├── storage                         <- local SQLite runtime storage
└── tests
```

## Prerequisites

- Python 3.12
- Docker
- Docker Compose
- DVC
- kubectl
- Minikube

Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Pull DVC artifacts if they are not present locally:

```bash
dvc pull
```

Expected local artifacts:

```text
data/raw/
models/best_model.pth
```

## Dataset

The project uses the Severstal Steel Defect Detection dataset structure:

- `data/raw/train.csv` contains run-length encoded masks
- `data/raw/train_images/` contains training images
- `data/raw/test_images/` contains test images
- each image may contain up to 4 defect classes

Large artifacts are tracked with DVC:

- `data/raw.dvc`
- `models/best_model.pth.dvc`

## Model

The baseline model is a multi-class segmentation model:

- architecture: U-Net
- encoder: EfficientNet-B4 in production config
- output channels: 4 defect classes
- checkpoint path: `models/best_model.pth`
- model registry name: `steel-defect-segmentation`

The notebook baseline is stored in:

```text
notebooks/defect-detection.ipynb
```

## Git Workflow

The repository follows GitHub Flow:

- `main` is the stable branch
- feature branches are created for isolated work
- changes are merged through Pull Requests
- commits use Conventional Commits

Examples:

```text
feat(api): add FastAPI inference service
feat(monitoring): add drift metrics and reports
feat(ui): add FastAPI web interface
feat(cd): add Argo CD application
fix(docker): install cpu-only pytorch in image
```

## FastAPI Inference Service

Run locally:

```bash
uvicorn defect_detection.api.main:app --reload
```

Open:

```text
Swagger/OpenAPI: http://127.0.0.1:8000/docs
Health:          http://127.0.0.1:8000/health
Readiness:       http://127.0.0.1:8000/ready
```

Main API endpoints:

- `POST /predict` - upload image and run inference
- `GET /predictions` - latest prediction history as JSON
- `POST /feedback` - submit true classes for concept drift
- `POST /retrain` - start a demo retraining job
- `GET /retrain/jobs` - latest retraining job history
- `GET /retrain/status/{job_id}` - get retraining job status
- `GET /drift/status` - current drift snapshot
- `GET /metrics` - Prometheus metrics

The `/predict` response includes:

- `prediction_id`
- image metadata
- tensor shape
- class-level predictions
- defect flags
- mask area
- RLE mask strings

## Web UI

Run the API and open the default Russian UI:

```text
Inference:   http://127.0.0.1:8000/ui
Predictions: http://127.0.0.1:8000/ui/predictions
Experiments: http://127.0.0.1:8000/ui/experiments
```

The English UI is available with the `lang=en` query parameter:

```text
Inference:   http://127.0.0.1:8000/ui?lang=en
Predictions: http://127.0.0.1:8000/ui/predictions?lang=en
Experiments: http://127.0.0.1:8000/ui/experiments?lang=en
```

The top navigation includes a `RU / EN` language switch.

The UI includes:

- selected image preview
- predicted mask overlay
- class result cards
- latest prediction table with thumbnails
- anomaly flags
- drift status flags
- drift warning notifications
- retraining trigger button
- latest retraining job status
- latest retraining job history
- MLflow run link after a successful demo job
- MLflow experiments entry point

## Docker

Build the API image:

```bash
docker build -t defect-detection-api:local .
```

Run the API container:

```bash
docker run --rm -p 8000:8000 defect-detection-api:local
```

The Dockerfile installs CPU-only PyTorch first to avoid CUDA packages in CI and
small local environments.

## Docker Compose

Run the API only:

```bash
docker compose up --build api
```

Run the full local debugging stack:

```bash
docker compose up --build
```

Services:

```text
API:        http://127.0.0.1:8000
MLflow:     http://127.0.0.1:5050
Prometheus: http://127.0.0.1:9090
Grafana:    http://127.0.0.1:3000
```

Grafana local credentials:

```text
admin / admin
```

## Runtime Storage

The API persists runtime state in SQLite:

```text
storage/app.db
```

The database stores:

- latest prediction history;
- feedback for concept drift calculation;
- demo retraining job statuses.

The database file is not committed to Git. In Docker Compose, the `storage/`
directory is mounted into the API container, so state survives container
restarts.

## MLflow

In Docker Compose, the API sends demo retraining runs to MLflow through the
internal `http://mlflow:5000` address, while the UI opens MLflow in the browser
through `http://127.0.0.1:5050`.

Start MLflow:

```bash
docker compose up -d mlflow
```

Log the baseline model run:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export no_proxy=localhost,127.0.0.1
export NO_PROXY=localhost,127.0.0.1

MLFLOW_TRACKING_URI=http://127.0.0.1:5050 \
  python -m defect_detection.modeling.train
```

The training entrypoint logs parameters, metrics, artifacts, and registers the
model as:

```text
steel-defect-segmentation
```

## Monitoring And Drift

Prometheus scrapes:

```text
http://api:8000/metrics
```

Prometheus config:

```text
monitoring/prometheus.yml
```

Useful Prometheus queries:

```promql
defect_api_requests_total
defect_api_request_latency_seconds
defect_predictions_total
defect_image_stat_value
defect_data_drift_value
defect_predicted_class_distribution_value
defect_target_drift_value
defect_feedback_total
defect_prediction_mismatch_total
defect_concept_drift_value
```

Data drift baseline:

```text
monitoring/reference_stats.json
```

Rebuild data drift baseline:

```bash
python -m defect_detection.monitoring.build_reference_stats \
  --image-dir data/raw/train_images \
  --output monitoring/reference_stats.json
```

Target drift baseline:

```text
monitoring/reference_target_distribution.json
```

Rebuild target drift baseline:

```bash
python -m defect_detection.monitoring.build_reference_target_distribution \
  --train-csv data/raw/train.csv \
  --output monitoring/reference_target_distribution.json
```

Concept drift is calculated from feedback:

```json
{
  "prediction_id": "<prediction_id from /predict>",
  "true_classes": [1, 3]
}
```

## Drift Reports

Generate a Markdown drift report from the running API:

```bash
python -m defect_detection.monitoring.report \
  --status-url http://127.0.0.1:8000/drift/status \
  --output-dir reports/drift
```

Generated reports are saved to:

```text
reports/drift/
```

## Kubernetes And Minikube

Start Minikube:

```bash
minikube start
```

Build the API image inside Minikube Docker:

```bash
eval $(minikube docker-env)
docker build -t defect-detection-api:local .
eval $(minikube docker-env -u)
```

Deploy MLflow to Minikube:

```bash
kubectl apply -f k8s/mlflow/
kubectl get pods
kubectl get svc
minikube service mlflow
```

For MLflow run links from the Web UI, expose MLflow with port-forward:

```bash
kubectl port-forward svc/mlflow 5000:5000
```

In another terminal, deploy the API:

```bash
kubectl apply -f k8s/api/
kubectl get pods
kubectl get svc
```

Open the API:

```bash
minikube service defect-detection-api
```

In Kubernetes, the API uses a `PersistentVolumeClaim` for `/app/storage`, so
SQLite runtime storage is not kept only inside the container filesystem. MLflow
also uses a `PersistentVolumeClaim` for `/mlflow`. The API sends demo retraining
runs to the internal Kubernetes service `http://mlflow:5000`.

## Argo CD GitOps Deployment

In this project, Argo CD is used for GitOps deployment of the FastAPI inference
service. MLflow also has Kubernetes manifests, but it is deployed separately
with `kubectl apply -f k8s/mlflow/`.

Install Argo CD in Minikube:

```bash
kubectl create namespace argocd
kubectl apply --server-side -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl get pods -n argocd
```

If the GitHub repository is private, create a fine-grained GitHub token with:

```text
Repository access: progmat64/defect-detection-system
Repository permissions: Contents read-only
```

Add repository credentials to Argo CD:

```bash
kubectl create secret generic defect-detection-repo \
  -n argocd \
  --from-literal=type=git \
  --from-literal=url=https://github.com/progmat64/defect-detection-system.git \
  --from-literal=username=progmat64 \
  --from-literal=password=<GITHUB_TOKEN> \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl label secret defect-detection-repo \
  -n argocd \
  argocd.argoproj.io/secret-type=repository \
  --overwrite
```

Apply the Argo CD Application:

```bash
kubectl apply -f k8s/argocd/application.yaml
kubectl get applications -n argocd
```

By default, the Application uses `targetRevision: main`. If the demo happens
before the feature branch is merged into `main`, temporarily point Argo CD to
the current branch:

```bash
kubectl patch application defect-detection-api -n argocd \
  --type merge \
  -p '{"spec":{"source":{"targetRevision":"feat/final-project-compliance"}}}'
```

Manual sync if needed:

```bash
kubectl patch application defect-detection-api -n argocd \
  --type merge \
  -p '{"operation":{"sync":{}}}'
```

Expected state:

```text
defect-detection-api   Synced   Healthy
```

Open Argo CD UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Browser:

```text
https://127.0.0.1:8080
```

Login:

```text
admin
```

Get the initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

## CI/CD

GitHub Actions workflow runs on pull requests to `main` and pushes to `main`.

The workflow performs:

- dependency installation
- Ruff linting
- pytest test suite
- model placeholder preparation for Docker build
- Docker image build

Workflow file:

```text
.github/workflows/ci.yml
```

## Tests And Checks

Run tests:

```bash
make test
```

Run linter:

```bash
make lint
```

Format code:

```bash
make format
```

## Notes

- Docker Compose is intended for local debugging.
- Kubernetes/Minikube is the target local production-like runtime.
- Argo CD uses Git as the source of truth for FastAPI Kubernetes manifests.
- MLflow in Minikube is deployed from separate manifests in `k8s/mlflow/`.
- `notebooks/*.ipynb` is excluded from GitHub language statistics through
  `.gitattributes`.
