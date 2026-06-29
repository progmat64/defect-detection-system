from prometheus_client import Counter, Gauge, Histogram

REQUESTS_TOTAL = Counter(
    "defect_api_requests_total",
    "Total number of API requests.",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY_SECONDS = Histogram(
    "defect_api_request_latency_seconds",
    "API request latency in seconds.",
    ["method", "endpoint"],
)

PREDICTIONS_TOTAL = Counter(
    "defect_predictions_total",
    "Total number of prediction requests.",
)

PREDICTED_DEFECT_IMAGES_TOTAL = Counter(
    "defect_predicted_defect_images_total",
    "Total number of images where at least one defect was predicted.",
)

PREDICTED_DEFECTS_BY_CLASS_TOTAL = Counter(
    "defect_predicted_defects_by_class_total",
    "Total number of predicted defects by class.",
    ["class_id"],
)

PREDICTED_CLASS_DISTRIBUTION_VALUE = Gauge(
    "defect_predicted_class_distribution_value",
    "Latest predicted defect class distribution.",
    ["class_id"],
)

IMAGE_STAT_VALUE = Gauge(
    "defect_image_stat_value",
    "Latest input image statistic value.",
    ["stat_name"],
)

DATA_DRIFT_VALUE = Gauge(
    "defect_data_drift_value",
    (
        "Absolute difference between current input image stats "
        "and reference stats."
    ),
    ["stat_name"],
)

TARGET_DRIFT_VALUE = Gauge(
    "defect_target_drift_value",
    (
        "Absolute difference between predicted and reference "
        "target distributions."
    ),
    ["class_id"],
)

FEEDBACK_TOTAL = Counter(
    "defect_feedback_total",
    "Total number of feedback records.",
)

PREDICTION_MISMATCH_TOTAL = Counter(
    "defect_prediction_mismatch_total",
    (
        "Total number of feedback records where prediction differs "
        "from true classes."
    ),
)

CONCEPT_DRIFT_VALUE = Gauge(
    "defect_concept_drift_value",
    "Current mismatch rate based on feedback records.",
)

RETRAINING_JOBS_TOTAL = Counter(
    "defect_retraining_jobs_total",
    "Total number of retraining jobs by status.",
    ["status"],
)

MODEL_RELOAD_TOTAL = Counter(
    "defect_model_reload_total",
    "Total number of successful model reloads in the API service.",
)

MODEL_INFO = Gauge(
    "defect_model_info",
    "Current model version loaded by the API service.",
    ["version", "path"],
)
