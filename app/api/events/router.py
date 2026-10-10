import uuid
from datetime import datetime
from typing import Annotated
from database.db_connect.db import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.events.schemas import EventCreate, EventRead
from services.events.service import EventService
from app.api.events.dependencies import EventServiceDependency


router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, service: EventServiceDependency):
    return await service.log(
        payload.job_id, payload.node, status=payload.status, payload=payload.payload_json
    )


@router.get("/job/{job_id}", response_model=list[EventRead])
async def list_job_events(
    job_id: uuid.UUID,
    service: EventServiceDependency,
    since: Annotated[datetime | None, Query(description="Только события позже этой метки")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
):
    """История событий джоба (для поллинга/SSE можно передавать since)."""
    return await service.list_by_job(job_id, since=since, limit=limit)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: uuid.UUID, service: EventServiceDependency):
    event = await service.get(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено")
    return event
