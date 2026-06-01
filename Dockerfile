FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY models/best_model.pth ./models/best_model.pth

ENV PYTHONPATH=/app/src
ENV NO_ALBUMENTATIONS_UPDATE=1

EXPOSE 8000

CMD ["uvicorn", "defect_detection.api.main:app", "--host", "0.0.0.0", "--port", "8000"]