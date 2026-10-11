import asyncio
import uuid
from datetime import datetime
from typing import Annotated
from database.db_connect.db import get_db
from database.models.jobs import JobStatus
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.events.schemas import EventCreate, EventRead
from app.api.events.dependencies import EventServiceDependency
from app.api.jobs.dependencies import JobServiceDependency
from services.events.service import EventService


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


@router.get("/job/{job_id}/stream")
async def stream_job_events(
    job_id: uuid.UUID,
    request: Request,
    service: EventServiceDependency,
    job_service: JobServiceDependency,
):
    """SSE-лента событий джоба для live-графа агентов.

    Отдаёт события по мере появления; завершается событием `done`, когда джоба
    перешла в терминальный статус (completed/failed/cancelled).
    """

    async def event_generator():
        last_ts: datetime | None = None
        while True:
            if await request.is_disconnected():
                break
            events = await service.list_by_job(job_id, since=last_ts, limit=100)
            for event in events:
                last_ts = event.ts
                yield f"data: {EventRead.model_validate(event).model_dump_json()}\n\n"
            job = await job_service.get(job_id)
            if job is None:
                yield 'event: error\ndata: {"detail": "job not found"}\n\n'
                break
            if (
                job.status
                in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
                and not events
            ):
                yield "event: done\ndata: {}\n\n"
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: uuid.UUID, service: EventServiceDependency):
    event = await service.get(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено")
    return event
