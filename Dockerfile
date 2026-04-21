FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir mlflow

COPY src ./src
COPY README.md .

ENV PYTHONPATH=/app/src

CMD ["python", "-c", "import defect_detection; print('defect_detection package import ok')"]
