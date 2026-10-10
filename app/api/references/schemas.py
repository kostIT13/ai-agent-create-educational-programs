import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReferenceCreate(BaseModel):
    course_id: uuid.UUID
    name: str = Field(max_length=512)
    s3_key: str = Field(max_length=1024)
    mime: str | None = Field(default=None, max_length=128)


class ReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    name: str
    mime: str | None
    s3_key: str
    created_at: datetime
