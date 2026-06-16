import base64
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from defect_detection.api.metrics import (
    CONCEPT_DRIFT_VALUE,
    DATA_DRIFT_VALUE,
    FEEDBACK_TOTAL,
    IMAGE_STAT_VALUE,
    PREDICTED_CLASS_DISTRIBUTION_VALUE,
    PREDICTED_DEFECT_IMAGES_TOTAL,
    PREDICTED_DEFECTS_BY_CLASS_TOTAL,
    PREDICTION_MISMATCH_TOTAL,
    PREDICTIONS_TOTAL,
    TARGET_DRIFT_VALUE,
)
from defect_detection.api.retraining import (
    create_retraining_job,
    run_retraining_job,
)
from defect_detection.api.schemas import FeedbackRequest
from defect_detection.api.storage import (
    get_prediction_classes,
    get_retraining_job,
    list_predictions,
    save_feedback,
    save_prediction,
    save_retraining_job,
)
from defect_detection.modeling.predict import decode_image, predict_image
from defect_detection.monitoring.drift import (
    DEFECT_CLASS_IDS,
    calculate_concept_drift_value,
    calculate_data_drift,
    calculate_drift_status,
    calculate_image_stats,
    calculate_prediction_target_distribution,
    calculate_target_drift,
    extract_predicted_classes,
    is_prediction_mismatch,
)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DATA_DRIFT_WARNING_THRESHOLD = 0.2
TARGET_DRIFT_WARNING_THRESHOLD = 0.2
CONCEPT_DRIFT_WARNING_THRESHOLD = 0.2

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/ready")
def readiness_check(request: Request):
    return {
        "model_loaded": getattr(request.app.state, "model", None) is not None
    }


@router.post("/predict")
async def predict(request: Request, file: Annotated[UploadFile, File()]):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}",
        )

    contents = await file.read()

    try:
        model = request.app.state.model
        reference_stats = request.app.state.reference_stats
        reference_target_distribution = (
            request.app.state.reference_target_distribution
        )
        image = decode_image(contents)
        image_stats = calculate_image_stats(image)
        data_drift = calculate_data_drift(image_stats, reference_stats)
        request.app.state.current_image_stats = image_stats
        request.app.state.current_data_drift = data_drift
        record_image_stats(image_stats)
        record_data_drift(data_drift)

        result = predict_image(model, contents)
        record_prediction_metrics(result["predictions"])
        predicted_target_distribution = (
            calculate_prediction_target_distribution(result["predictions"])
        )
        target_drift = calculate_target_drift(
            predicted_target_distribution,
            reference_target_distribution,
        )
        request.app.state.current_target_distribution = (
            predicted_target_distribution
        )
        request.app.state.current_target_drift = target_drift
        record_predicted_class_distribution(predicted_target_distribution)
        record_target_drift(target_drift)
        prediction_id = str(uuid4())
        predicted_classes = extract_predicted_classes(result["predictions"])
        save_prediction(
            request.app.state.db,
            {
                "prediction_id": prediction_id,
                "created_at": datetime.now(UTC).isoformat(),
                "filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(contents),
                "image_preview": build_image_preview_data_url(
                    file.content_type,
                    contents,
                ),
                "predicted_classes": predicted_classes,
                "has_any_defect": bool(predicted_classes),
            },
        )
    except AttributeError as exc:
        raise HTTPException(
            status_code=503, detail="Model is not loaded"
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "prediction_id": prediction_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
        **result,
    }


@router.get("/predictions")
def prediction_history(request: Request):
    return {
        "items": list_predictions(request.app.state.db),
    }


@router.post("/feedback")
def submit_feedback(request: Request, feedback: FeedbackRequest):
    invalid_classes = [
        class_id
        for class_id in feedback.true_classes
        if class_id not in DEFECT_CLASS_IDS
    ]

    if invalid_classes:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid defect classes: {invalid_classes}",
        )

    predicted_classes = get_prediction_classes(
        request.app.state.db,
        feedback.prediction_id
    )

    if predicted_classes is None:
        raise HTTPException(status_code=404, detail="Prediction not found")

    mismatch = is_prediction_mismatch(predicted_classes, feedback.true_classes)
    save_feedback(
        request.app.state.db,
        prediction_id=feedback.prediction_id,
        created_at=datetime.now(UTC).isoformat(),
        true_classes=feedback.true_classes,
        is_mismatch=mismatch,
    )
    request.app.state.feedback_total += 1
    FEEDBACK_TOTAL.inc()

    if mismatch:
        request.app.state.feedback_mismatch_total += 1
        PREDICTION_MISMATCH_TOTAL.inc()

    concept_drift_value = calculate_concept_drift_value(
        feedback_total=request.app.state.feedback_total,
        mismatch_total=request.app.state.feedback_mismatch_total,
    )
    request.app.state.current_concept_drift = concept_drift_value
    CONCEPT_DRIFT_VALUE.set(concept_drift_value)

    return {
        "prediction_id": feedback.prediction_id,
        "predicted_classes": predicted_classes,
        "true_classes": feedback.true_classes,
        "is_mismatch": mismatch,
        "concept_drift_value": concept_drift_value,
    }


@router.post("/retrain")
def trigger_retraining(
    request: Request,
    background_tasks: BackgroundTasks,
):
    job = create_retraining_job()
    save_retraining_job(request.app.state.db, job)

    background_tasks.add_task(
        run_retraining_job,
        job,
        request.app.state.db,
    )

    return job


@router.get("/retrain/status/{job_id}")
def retraining_status(request: Request, job_id: str):
    job = get_retraining_job(request.app.state.db, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Retraining job not found")

    return job


@router.get("/drift/status")
def drift_status(request: Request):
    concept_drift_values = {}

    if request.app.state.feedback_total > 0:
        concept_drift_values = {
            "mismatch_rate": request.app.state.current_concept_drift,
        }

    reference_distribution = request.app.state.reference_target_distribution
    current_distribution = request.app.state.current_target_distribution

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "data_drift": {
            "status": calculate_drift_status(
                request.app.state.current_data_drift,
                DATA_DRIFT_WARNING_THRESHOLD,
            ),
            "threshold": DATA_DRIFT_WARNING_THRESHOLD,
            "reference_stats": request.app.state.reference_stats,
            "current_stats": request.app.state.current_image_stats,
            "drift_values": request.app.state.current_data_drift,
        },
        "target_drift": {
            "status": calculate_drift_status(
                request.app.state.current_target_drift,
                TARGET_DRIFT_WARNING_THRESHOLD,
            ),
            "threshold": TARGET_DRIFT_WARNING_THRESHOLD,
            "reference_distribution": reference_distribution,
            "current_distribution": current_distribution,
            "drift_values": request.app.state.current_target_drift,
        },
        "concept_drift": {
            "status": calculate_drift_status(
                concept_drift_values,
                CONCEPT_DRIFT_WARNING_THRESHOLD,
            ),
            "threshold": CONCEPT_DRIFT_WARNING_THRESHOLD,
            "feedback_total": request.app.state.feedback_total,
            "mismatch_total": request.app.state.feedback_mismatch_total,
            "drift_value": request.app.state.current_concept_drift,
        },
    }


@router.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def record_prediction_metrics(predictions: list[dict[str, object]]) -> None:
    PREDICTIONS_TOTAL.inc()

    has_any_defect = any(item["has_defect"] for item in predictions)

    if has_any_defect:
        PREDICTED_DEFECT_IMAGES_TOTAL.inc()

    for item in predictions:
        if item["has_defect"]:
            PREDICTED_DEFECTS_BY_CLASS_TOTAL.labels(
                class_id=str(item["class_id"])
            ).inc()


def record_image_stats(stats: dict[str, float]) -> None:
    for stat_name, value in stats.items():
        IMAGE_STAT_VALUE.labels(stat_name=stat_name).set(value)


def record_data_drift(drift_values: dict[str, float]) -> None:
    for stat_name, value in drift_values.items():
        DATA_DRIFT_VALUE.labels(stat_name=stat_name).set(value)


def record_predicted_class_distribution(
    distribution: dict[str, float],
) -> None:
    for class_id, value in distribution.items():
        PREDICTED_CLASS_DISTRIBUTION_VALUE.labels(class_id=class_id).set(value)


def record_target_drift(drift_values: dict[str, float]) -> None:
    for class_id, value in drift_values.items():
        TARGET_DRIFT_VALUE.labels(class_id=class_id).set(value)


def build_image_preview_data_url(content_type: str, contents: bytes) -> str:
    encoded = base64.b64encode(contents).decode("ascii")
    return f"data:{content_type};base64,{encoded}"
