from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile

from defect_detection.modeling.predict import load_model, predict_image

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pth"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model(MODEL_PATH)
    yield


app = FastAPI(title="Defect Detection API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/ready")
def readiness_check():
    return {"model_loaded": getattr(app.state, "model", None) is not None}


@app.post("/predict")
async def predict(file: Annotated[UploadFile, File()]):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}",
        )

    contents = await file.read()

    try:
        model = app.state.model
        result = predict_image(model, contents)
    except AttributeError as exc:
        raise HTTPException(status_code=503, detail="Model is not loaded") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
        **result,
    }
