"""Pydantic-схемы для эндпоинтов джобов."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from database.models.jobs import JobStatus


class JobCreate(BaseModel):
    course_id: uuid.UUID


class JobFail(BaseModel):
    error: str


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    status: JobStatus
    progress: int
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class JobProgressUpdate(BaseModel):
    progress: int = Field(ge=0, le=100)
