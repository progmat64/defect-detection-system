from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    prediction_id: str
    true_classes: list[int] = Field(default_factory=list)
