import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CourseVersionCreate(BaseModel):
    course_id: uuid.UUID
    graph_json: dict
    diff_json: dict | None = None


class CourseVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    version: int
    graph_json: dict
    diff_json: dict | None
    created_at: datetime
