import uuid
from datetime import datetime
from typing import Annotated
from database.db_connect.db import get_db
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.usage_log.schemas import (
    UsageByModelRow,
    UsageLogCreate,
    UsageLogRead,
    UsageTotals,
)
from app.api.usage_log.dependencies import UsageLogServiceDependency


router = APIRouter(prefix="/usage-log", tags=["usage-log"])


@router.post("", response_model=UsageLogRead, status_code=status.HTTP_201_CREATED)
async def create_usage_log(payload: UsageLogCreate, service: UsageLogServiceDependency):
    return await service.log_request(
        payload.course_id,
        payload.model,
        tokens_in=payload.tokens_in,
        tokens_out=payload.tokens_out,
        cost=payload.cost,
    )


@router.get("/course/{course_id}", response_model=list[UsageLogRead])
async def list_course_usage(course_id: uuid.UUID, service: UsageLogServiceDependency):
    return await service.list_by_course(course_id)


@router.get("/totals", response_model=UsageTotals)
async def get_usage_totals(
    service: UsageLogServiceDependency,
    since: Annotated[datetime | None, Query()] = None,
    until: Annotated[datetime | None, Query()] = None,
):
    """Суммарный расход токенов/стоимости за период."""
    return await service.totals(since=since, until=until)


@router.get("/by-model", response_model=list[UsageByModelRow])
async def get_usage_by_model(
    service: UsageLogServiceDependency,
    since: Annotated[datetime | None, Query()] = None,
    until: Annotated[datetime | None, Query()] = None,
):
    """Разбивка расхода по моделям за период."""
    rows = await service.totals_by_model(since=since, until=until)
    return [
        UsageByModelRow(model=m, tokens_in=ti, tokens_out=to, cost=c)
        for m, ti, to, c in rows
    ]
