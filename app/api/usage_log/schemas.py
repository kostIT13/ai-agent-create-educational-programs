import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class UsageLogCreate(BaseModel):
    course_id: uuid.UUID
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost: Decimal = Decimal("0")


class UsageLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    model: str
    tokens_in: int
    tokens_out: int
    cost: Decimal
    ts: datetime


class UsageTotals(BaseModel):
    tokens_in: int
    tokens_out: int
    cost: Decimal
    requests: int


class UsageByModelRow(BaseModel):
    model: str
    tokens_in: int
    tokens_out: int
    cost: Decimal
