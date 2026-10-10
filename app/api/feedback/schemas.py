import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from database.models.feedback import Feedback


class FeedbackCreate(BaseModel):
    course_id: uuid.UUID
    entity_id: str = Field(max_length=64)
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
    created_by: uuid.UUID | None = None


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    entity_id: str
    rating: int
    comment: str | None
    created_by: uuid.UUID | None
    created_at: datetime


class FeedbackStatsRow(BaseModel):
    entity_id: str
    avg_rating: float
    count: int


class FeedbackStats(BaseModel):
    course_id: uuid.UUID
    items: list[FeedbackStatsRow]
