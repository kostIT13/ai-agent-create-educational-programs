import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from database.models.events import EventStatus


class EventCreate(BaseModel):
    job_id: uuid.UUID
    node: str
    status: EventStatus = EventStatus.STARTED
    payload_json: dict = {}


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    node: str
    status: EventStatus
    payload_json: dict
    ts: datetime
