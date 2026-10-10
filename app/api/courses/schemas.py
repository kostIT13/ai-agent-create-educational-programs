import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from database.models.courses import CourseStatus


class CourseCreate(BaseModel):
    title: str = Field(max_length=512)
    brief_json: dict = Field(default_factory=dict)
    created_by: uuid.UUID | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=512)
    brief_json: dict | None = None


class CourseStatusUpdate(BaseModel):
    status: CourseStatus


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    brief_json: dict
    status: CourseStatus
    created_by: uuid.UUID | None
    version: int
    created_at: datetime
    updated_at: datetime


class CourseListRead(BaseModel):
    items: list[CourseRead]
    total: int
    limit: int
    offset: int
