# Drift Reports

Эта директория предназначена для Markdown-отчетов о дрейфе модели.

Отчеты генерируются вручную на основе текущего состояния endpoint:

```text
GET /drift/status
```

Такой формат оставляет генерацию отчета воспроизводимой: snapshot дрейфа можно
получить из запущенного API или сохранить в JSON-файл и пересоздать отчет позже.

## Генерация из запущенного API

Сначала запустите API:

```bash
PYTHONPATH=src uvicorn defect_detection.api.main:app --reload
```

Сгенерируйте отчет:

```bash
PYTHONPATH=src python -m defect_detection.monitoring.report \
  --status-url http://127.0.0.1:8000/drift/status \
  --output-dir reports/drift
```

Результат будет сохранен в файл вида:

```text
reports/drift/drift_report_<timestamp>.md
```

## Генерация из JSON-файла

Если snapshot нужно сохранить отдельно:

```bash
curl http://127.0.0.1:8000/drift/status \
  -o reports/drift/status_snapshot.json
```

После этого отчет можно создать из локального файла:

```bash
PYTHONPATH=src python -m defect_detection.monitoring.report \
  --status-json reports/drift/status_snapshot.json \
  --output-dir reports/drift
```

## Что входит в отчет

Отчет содержит:

- статус data drift;
- статус target drift;
- статус concept drift;
- reference/baseline values;
- current values;
- drift values;
- thresholds;
- feedback counters для concept drift.

