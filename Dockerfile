FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch \
    torchvision \
    && grep -v -E "^(torch|torchvision)$" requirements.txt > /tmp/requirements-docker.txt \
    && pip install --no-cache-dir -r /tmp/requirements-docker.txt \
    && rm /tmp/requirements-docker.txt

COPY src ./src
COPY monitoring/reference_stats.json ./monitoring/reference_stats.json
COPY monitoring/reference_target_distribution.json ./monitoring/reference_target_distribution.json
COPY monitoring/reference_features.csv ./monitoring/reference_features.csv
COPY models/best_model.pth ./models/best_model.pth

ENV PYTHONPATH=/app/src
ENV NO_ALBUMENTATIONS_UPDATE=1
ENV ALLOW_MODEL_PLACEHOLDER=1

EXPOSE 8000

CMD ["uvicorn", "defect_detection.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
