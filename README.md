# Defect Detection System

Английская версия: [README.en.md](README.en.md).

Воспроизводимая MLOps-система для сегментации дефектов на поверхности стали.
Проект закрывает production-like цикл эксплуатации ML-модели: версионирование
данных и модели, трекинг экспериментов, inference-сервис, Docker/Kubernetes
деплой, мониторинг дрейфа, отчеты, Web UI и GitOps-доставка через Argo CD.

## Что входит в проект

- Датасет: Severstal Steel Defect Detection
- Модель: U-Net для сегментации 4 классов дефектов
- Структура проекта: стиль Cookiecutter Data Science
- Версионирование: GitHub Flow, Conventional Commits, DVC
- Трекинг экспериментов: MLflow Tracking и Model Registry
- API: FastAPI с OpenAPI, health/readiness checks и image inference
- Runtime storage: SQLite для истории предсказаний, feedback и retraining jobs
- Упаковка: Docker image и Docker Compose для локальной отладки
- Kubernetes: манифесты API и MLflow для Minikube
- Мониторинг: Prometheus metrics и Grafana dashboards
- Drift: data drift, target drift, concept drift
- Отчеты: генерация Markdown-отчетов о дрейфе
- Web UI: страница инференса, история предсказаний, drift alerts
- CD: Argo CD Application для GitOps-деплоя в Minikube

## Структура репозитория

```text
├── data
│   ├── external
│   ├── interim
│   ├── processed
│   └── raw                         <- датасет под DVC
├── k8s
│   ├── api                         <- Kubernetes manifests FastAPI
│   ├── argocd                      <- Argo CD Application manifest
│   └── mlflow                      <- Kubernetes manifests MLflow
├── models                          <- model artifacts под DVC
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
│   ├── modeling                    <- train/inference code
│   ├── monitoring                  <- drift/report utilities
│   ├── config.py
│   ├── dataset.py
│   ├── features.py
│   └── plots.py
├── storage                         <- local SQLite runtime storage
└── tests
```

## Требования

- Python 3.12
- Docker
- Docker Compose
- DVC
- kubectl
- Minikube

Установка Python-зависимостей:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Если локально нет данных или модели, подтянуть DVC-артефакты:

```bash
dvc pull
```

Ожидаемые локальные артефакты:

```text
data/raw/
models/best_model.pth
```

## Датасет

Проект использует структуру датасета Severstal Steel Defect Detection:

- `data/raw/train.csv` содержит маски в формате RLE
- `data/raw/train_images/` содержит train-изображения
- `data/raw/test_images/` содержит test-изображения
- на изображении может быть до 4 классов дефектов

Крупные артефакты версионируются через DVC:

- `data/raw.dvc`
- `models/best_model.pth.dvc`

## Модель

Baseline-модель решает задачу multi-class segmentation:

- архитектура: U-Net
- encoder: EfficientNet-B4 в production-конфиге
- output channels: 4 класса дефектов
- checkpoint: `models/best_model.pth`
- имя модели в registry: `steel-defect-segmentation`

Baseline notebook:

```text
notebooks/defect-detection.ipynb
```

## Git workflow

Репозиторий использует GitHub Flow:

- `main` - стабильная ветка
- новая работа делается в feature-ветках
- изменения попадают в `main` через Pull Request
- коммиты оформляются в стиле Conventional Commits

Примеры:

```text
feat(api): add FastAPI inference service
feat(monitoring): add drift metrics and reports
feat(ui): add FastAPI web interface
feat(cd): add Argo CD application
fix(docker): install cpu-only pytorch in image
```

## FastAPI inference service

Локальный запуск:

```bash
uvicorn defect_detection.api.main:app --reload
```

Открыть:

```text
Swagger/OpenAPI: http://127.0.0.1:8000/docs
Health:          http://127.0.0.1:8000/health
Readiness:       http://127.0.0.1:8000/ready
```

Основные API endpoints:

- `POST /predict` - загрузить изображение и получить prediction
- `GET /predictions` - история последних предсказаний в JSON
- `POST /feedback` - отправить true classes для concept drift
- `POST /retrain` - запустить demo retraining job
- `GET /retrain/status/{job_id}` - получить статус retraining job
- `GET /drift/status` - текущий snapshot drift-состояния
- `GET /metrics` - Prometheus metrics

Ответ `/predict` содержит:

- `prediction_id`
- metadata изображения
- tensor shape
- predictions по классам
- defect flags
- площадь маски
- RLE-строки масок

## Web UI

Запустить API и открыть русскую версию интерфейса:

```text
Инференс:      http://127.0.0.1:8000/ui
Предсказания:  http://127.0.0.1:8000/ui/predictions
Эксперименты:  http://127.0.0.1:8000/ui/experiments
```

Английская версия доступна через параметр `lang=en`:

```text
Inference:   http://127.0.0.1:8000/ui?lang=en
Predictions: http://127.0.0.1:8000/ui/predictions?lang=en
Experiments: http://127.0.0.1:8000/ui/experiments?lang=en
```

В верхней навигации есть переключатель `RU / EN`.

UI включает:

- предпросмотр выбранного изображения
- overlay предсказанной маски
- карточки результатов по классам
- таблицу последних предсказаний с thumbnail
- флаги аномалий
- статусы дрейфа
- уведомления о дрейфе
- кнопку запуска переобучения
- статус последней retraining job
- ссылку на MLflow experiments

## Docker

Собрать API image:

```bash
docker build -t defect-detection-api:local .
```

Запустить API container:

```bash
docker run --rm -p 8000:8000 defect-detection-api:local
```

Dockerfile сначала устанавливает CPU-only PyTorch, чтобы не тянуть CUDA-пакеты
в CI и локальных окружениях с ограниченным диском.

## Docker Compose

Запустить только API:

```bash
docker compose up --build api
```

Запустить весь локальный стек для отладки:

```bash
docker compose up --build
```

Сервисы:

```text
API:        http://127.0.0.1:8000
MLflow:     http://127.0.0.1:5050
Prometheus: http://127.0.0.1:9090
Grafana:    http://127.0.0.1:3000
```

Локальные credentials Grafana:

```text
admin / admin
```

## Runtime storage

API хранит runtime-состояние в SQLite:

```text
storage/app.db
```

В базе сохраняются:

- история последних предсказаний;
- feedback для расчета concept drift;
- статусы demo retraining jobs.

Файл базы данных не коммитится в Git. В Docker Compose директория `storage/`
монтируется внутрь API container, поэтому состояние сохраняется между
перезапусками контейнера.

## MLflow

Запустить MLflow:

```bash
docker compose up -d mlflow
```

Залогировать baseline run:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export no_proxy=localhost,127.0.0.1
export NO_PROXY=localhost,127.0.0.1

MLFLOW_TRACKING_URI=http://127.0.0.1:5050 \
  python -m defect_detection.modeling.train
```

Training entrypoint логирует параметры, метрики, artifacts и регистрирует
модель:

```text
steel-defect-segmentation
```

## Monitoring и drift

Prometheus собирает метрики с:

```text
http://api:8000/metrics
```

Конфиг Prometheus:

```text
monitoring/prometheus.yml
```

Полезные Prometheus queries:

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

Baseline для data drift:

```text
monitoring/reference_stats.json
```

Пересчитать baseline для data drift:

```bash
python -m defect_detection.monitoring.build_reference_stats \
  --image-dir data/raw/train_images \
  --output monitoring/reference_stats.json
```

Baseline для target drift:

```text
monitoring/reference_target_distribution.json
```

Пересчитать baseline для target drift:

```bash
python -m defect_detection.monitoring.build_reference_target_distribution \
  --train-csv data/raw/train.csv \
  --output monitoring/reference_target_distribution.json
```

Concept drift считается на основе feedback:

```json
{
  "prediction_id": "<prediction_id from /predict>",
  "true_classes": [1, 3]
}
```

## Drift reports

Сгенерировать Markdown-отчет о дрейфе из запущенного API:

```bash
python -m defect_detection.monitoring.report \
  --status-url http://127.0.0.1:8000/drift/status \
  --output-dir reports/drift
```

Отчеты сохраняются в:

```text
reports/drift/
```

## Kubernetes и Minikube

Запустить Minikube:

```bash
minikube start
```

Собрать API image внутри Docker окружения Minikube:

```bash
eval $(minikube docker-env)
docker build -t defect-detection-api:local .
eval $(minikube docker-env -u)
```

Задеплоить API:

```bash
kubectl apply -f k8s/api/
kubectl get pods
kubectl get svc
```

Открыть API:

```bash
minikube service defect-detection-api
```

Задеплоить MLflow в Minikube:

```bash
kubectl apply -f k8s/mlflow/
kubectl get pods
kubectl get svc
minikube service mlflow
```

## Argo CD GitOps deployment

В проекте Argo CD используется для GitOps-деплоя FastAPI inference service.
MLflow также имеет Kubernetes manifests, но деплоится отдельной командой через
`kubectl apply -f k8s/mlflow/`.

Установить Argo CD в Minikube:

```bash
kubectl create namespace argocd
kubectl apply --server-side -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl get pods -n argocd
```

Если GitHub-репозиторий private, создать fine-grained GitHub token:

```text
Repository access: progmat64/defect-detection-system
Repository permissions: Contents read-only
```

Добавить credentials репозитория в Argo CD:

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

Применить Argo CD Application:

```bash
kubectl apply -f k8s/argocd/application.yaml
kubectl get applications -n argocd
```

Если нужен ручной sync:

```bash
kubectl patch application defect-detection-api -n argocd \
  --type merge \
  -p '{"operation":{"sync":{}}}'
```

Ожидаемое состояние:

```text
defect-detection-api   Synced   Healthy
```

Открыть Argo CD UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Браузер:

```text
https://127.0.0.1:8080
```

Логин:

```text
admin
```

Получить initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

## CI/CD

GitHub Actions workflow запускается на Pull Request в `main` и push в `main`.

Workflow выполняет:

- установку dependencies
- Ruff linting
- pytest test suite
- подготовку model placeholder для Docker build
- Docker image build

Workflow file:

```text
.github/workflows/ci.yml
```

## Тесты и проверки

Запустить тесты:

```bash
make test
```

Запустить linter:

```bash
make lint
```

Отформатировать код:

```bash
make format
```

## Примечания

- Docker Compose используется для локальной отладки.
- Kubernetes/Minikube используется как production-like runtime.
- Argo CD использует Git как source of truth для FastAPI Kubernetes manifests.
- MLflow в Minikube деплоится отдельными Kubernetes manifests из `k8s/mlflow/`.
- `notebooks/*.ipynb` исключены из GitHub language statistics через
  `.gitattributes`.
