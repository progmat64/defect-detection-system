DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = {"en", "ru"}

PAGE_PATHS = {
    "inference": "/ui",
    "predictions": "/ui/predictions",
    "experiments": "/ui/experiments",
}

TRANSLATIONS = {
    "ru": {
        "anomaly": "Аномалия",
        "app_title": "Обнаружение дефектов",
        "area": "Площадь",
        "class": "Класс",
        "class_label": "Класс",
        "classes": "Классы",
        "clean": "чисто",
        "concept_drift": "Дрейф концепции",
        "created": "Создано",
        "data_drift": "Дрейф данных",
        "defect": "Дефект",
        "defect_found": "дефект",
        "defect_no": "нет",
        "defect_yes": "да",
        "drift_status_label": "Статус дрейфа",
        "drift_warning": "Предупреждение о дрейфе",
        "experiments_subtitle": "Точки входа в трекинг и реестр моделей.",
        "experiments_title": "Эксперименты",
        "file": "Файл",
        "image_formats": "JPEG, PNG, WEBP",
        "image_preview": "Предпросмотр изображения",
        "image_title": "Изображение",
        "inference_subtitle": (
            "Загрузите изображение поверхности стали и проверьте результат "
            "модели."
        ),
        "inference_title": "Инференс",
        "json": "JSON",
        "language_en": "EN",
        "language_ru": "RU",
        "local_ui": "Локальный UI",
        "model_registry": "Реестр моделей",
        "nav_experiments": "Эксперименты",
        "nav_inference": "Инференс",
        "nav_openapi": "OpenAPI",
        "nav_predictions": "Предсказания",
        "no_prediction": "Предсказаний пока нет.",
        "no_predictions_yet": "Предсказаний пока нет.",
        "no_retraining_jobs_yet": "Запусков переобучения пока нет.",
        "none": "нет",
        "open_mlflow": "Открыть MLflow",
        "open_mlflow_run": "Открыть run",
        "predict": "Предсказать",
        "prediction_complete": "Предсказание готово.",
        "prediction_failed": "Не удалось выполнить предсказание.",
        "prediction_id": "ID предсказания",
        "predictions_subtitle": (
            "Последние записи инференса из SQLite runtime storage."
        ),
        "predictions_title": "Предсказания",
        "preview": "Превью",
        "registered_model": "Зарегистрированная модель",
        "retraining_failed": "Не удалось запустить переобучение.",
        "retraining_started": "Переобучение запущено.",
        "retraining_status": "Переобучение",
        "retraining_status_failed": (
            "Не удалось получить статус переобучения."
        ),
        "retraining_succeeded": "Переобучение завершено.",
        "retraining_jobs_title": "Переобучение",
        "result_title": "Результат",
        "run_retraining": "Запустить переобучение",
        "running_inference": "Выполняется инференс...",
        "select_image": "Выбрать изображение",
        "select_image_first": "Сначала выберите изображение.",
        "status_failed": "ошибка",
        "status_no_data": "нет данных",
        "status_ok": "норма",
        "status_queued": "в очереди",
        "status_running": "выполняется",
        "status_succeeded": "завершено",
        "status_warning": "внимание",
        "status": "Статус",
        "target_drift": "Дрейф целевой переменной",
        "tracking_uri": "Tracking URI",
        "waiting_for_input": "Ожидание изображения",
        "waiting_for_model": "Ожидание результата модели",
    },
    "en": {
        "anomaly": "Anomaly",
        "app_title": "Defect Detection",
        "area": "Area",
        "class": "Class",
        "class_label": "Class",
        "classes": "Classes",
        "clean": "clean",
        "concept_drift": "Concept drift",
        "created": "Created",
        "data_drift": "Data drift",
        "defect": "Defect",
        "defect_found": "defect",
        "defect_no": "no",
        "defect_yes": "yes",
        "drift_status_label": "Drift status",
        "drift_warning": "Drift warning",
        "experiments_subtitle": "Model tracking and registry entry points.",
        "experiments_title": "Experiments",
        "file": "File",
        "image_formats": "JPEG, PNG, WEBP",
        "image_preview": "Image preview",
        "image_title": "Image",
        "inference_subtitle": (
            "Upload a steel surface image and inspect model output."
        ),
        "inference_title": "Inference",
        "json": "JSON",
        "language_en": "EN",
        "language_ru": "RU",
        "local_ui": "Local UI",
        "model_registry": "Model registry",
        "nav_experiments": "Experiments",
        "nav_inference": "Inference",
        "nav_openapi": "OpenAPI",
        "nav_predictions": "Predictions",
        "no_prediction": "No prediction yet.",
        "no_predictions_yet": "No predictions yet.",
        "no_retraining_jobs_yet": "No retraining jobs yet.",
        "none": "none",
        "open_mlflow": "Open MLflow",
        "open_mlflow_run": "Open run",
        "predict": "Predict",
        "prediction_complete": "Prediction complete.",
        "prediction_failed": "Prediction failed.",
        "prediction_id": "Prediction ID",
        "predictions_subtitle": (
            "Latest inference records from SQLite runtime storage."
        ),
        "predictions_title": "Predictions",
        "preview": "Preview",
        "registered_model": "Registered model",
        "retraining_failed": "Failed to start retraining.",
        "retraining_started": "Retraining has started.",
        "retraining_status": "Retraining",
        "retraining_status_failed": "Failed to fetch retraining status.",
        "retraining_succeeded": "Retraining completed.",
        "retraining_jobs_title": "Retraining",
        "result_title": "Result",
        "run_retraining": "Run retraining",
        "running_inference": "Running inference...",
        "select_image": "Select image",
        "select_image_first": "Select an image first.",
        "status_failed": "failed",
        "status_no_data": "no data",
        "status_ok": "ok",
        "status_queued": "queued",
        "status_running": "running",
        "status_succeeded": "succeeded",
        "status_warning": "warning",
        "status": "Status",
        "target_drift": "Target drift",
        "tracking_uri": "Tracking URI",
        "waiting_for_input": "Waiting for input",
        "waiting_for_model": "Waiting for model output",
    },
}


def normalize_language(language: str | None) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language

    return DEFAULT_LANGUAGE


def get_translations(language: str | None) -> tuple[str, dict[str, str]]:
    normalized_language = normalize_language(language)
    return normalized_language, TRANSLATIONS[normalized_language]


def build_page_urls(language: str) -> dict[str, str]:
    return {
        page: f"{path}?lang={language}" for page, path in PAGE_PATHS.items()
    }


def build_language_urls(active_page: str) -> dict[str, str]:
    path = PAGE_PATHS[active_page]
    return {
        language: f"{path}?lang={language}"
        for language in sorted(SUPPORTED_LANGUAGES)
    }
