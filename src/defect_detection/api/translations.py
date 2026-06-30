DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = {"en", "ru"}

PAGE_PATHS = {
    "inference": "/ui",
    "predictions": "/ui/predictions",
    "drift_reports": "/ui/drift-reports",
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
        "current_checkpoint": "Текущий checkpoint",
        "current_model": "Текущая модель в сервисе",
        "current_model_version": "Текущая версия",
        "data_drift": "Дрейф данных",
        "defect": "Дефект",
        "defect_found": "дефект",
        "defect_no": "нет",
        "defect_yes": "да",
        "drift_status_label": "Статус дрейфа",
        "drift_report": "Отчет о дрейфе",
        "drift_reports_subtitle": (
            "Markdown-отчеты из текущего drift snapshot API."
        ),
        "drift_reports_title": "Отчеты о дрейфе",
        "drift_warning": "Предупреждение о дрейфе",
        "download": "Скачать",
        "experiments_subtitle": "Точки входа в трекинг и реестр моделей.",
        "experiments_title": "Эксперименты",
        "feedback": "Feedback",
        "feedback_failed": "Не удалось отправить feedback.",
        "feedback_saved": "Feedback сохранен.",
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
        "nav_drift_reports": "Отчеты",
        "nav_inference": "Инференс",
        "nav_openapi": "OpenAPI",
        "nav_predictions": "Предсказания",
        "no_prediction": "Предсказаний пока нет.",
        "no_predictions_yet": "Предсказаний пока нет.",
        "no_drift_reports_yet": "Отчетов о дрейфе пока нет.",
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
        "generate_drift_report": "Сгенерировать отчет",
        "evidently_reports_title": "Отчеты Evidently",
        "evidently_reports_subtitle": (
            "Статистические отчеты о дрейфе данных (KS-тесты) "
            "по последним предсказаниям."
        ),
        "evidently_missing_reference": (
            "Не удалось создать Evidently-отчет: reference feature table "
            "не загружена в API."
        ),
        "evidently_not_enough_samples": (
            "Не удалось создать Evidently-отчет: сначала выполните минимум "
            "{min_samples} инференсов."
        ),
        "evidently_report_created": "Evidently-отчет создан.",
        "generate_evidently_report": "Сгенерировать Evidently-отчет",
        "no_evidently_reports_yet": "Отчетов Evidently пока нет.",
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
        "status_rejected": "отклонено",
        "status_running": "выполняется",
        "status_succeeded": "завершено",
        "status_warning": "внимание",
        "status": "Статус",
        "open": "Открыть",
        "submit_feedback": "Отправить feedback",
        "target_drift": "Дрейф целевой переменной",
        "tracking_uri": "Tracking URI",
        "true_classes": "Истинные классы",
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
        "current_checkpoint": "Current checkpoint",
        "current_model": "Current service model",
        "current_model_version": "Current version",
        "data_drift": "Data drift",
        "defect": "Defect",
        "defect_found": "defect",
        "defect_no": "no",
        "defect_yes": "yes",
        "drift_status_label": "Drift status",
        "drift_report": "Drift report",
        "drift_reports_subtitle": (
            "Markdown reports generated from the current drift snapshot API."
        ),
        "drift_reports_title": "Drift reports",
        "drift_warning": "Drift warning",
        "download": "Download",
        "experiments_subtitle": "Model tracking and registry entry points.",
        "experiments_title": "Experiments",
        "feedback": "Feedback",
        "feedback_failed": "Failed to submit feedback.",
        "feedback_saved": "Feedback saved.",
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
        "nav_drift_reports": "Reports",
        "nav_inference": "Inference",
        "nav_openapi": "OpenAPI",
        "nav_predictions": "Predictions",
        "no_prediction": "No prediction yet.",
        "no_predictions_yet": "No predictions yet.",
        "no_drift_reports_yet": "No drift reports yet.",
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
        "generate_drift_report": "Generate report",
        "evidently_reports_title": "Evidently reports",
        "evidently_reports_subtitle": (
            "Statistical data drift reports (KS tests) "
            "over recent predictions."
        ),
        "evidently_missing_reference": (
            "Failed to create Evidently report: the reference feature table "
            "is not loaded by the API."
        ),
        "evidently_not_enough_samples": (
            "Failed to create Evidently report: run at least "
            "{min_samples} inferences first."
        ),
        "evidently_report_created": "Evidently report created.",
        "generate_evidently_report": "Generate Evidently report",
        "no_evidently_reports_yet": "No Evidently reports yet.",
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
        "status_rejected": "rejected",
        "status_running": "running",
        "status_succeeded": "succeeded",
        "status_warning": "warning",
        "status": "Status",
        "open": "Open",
        "submit_feedback": "Submit feedback",
        "target_drift": "Target drift",
        "tracking_uri": "Tracking URI",
        "true_classes": "True classes",
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
