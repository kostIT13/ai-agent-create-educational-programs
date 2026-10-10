import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.events import Event, EventStatus
from services.events.base import AbstractEventRepository
from services.events.repository import EventRepository


class EventService:
    def __init__(
        self,
        session: AsyncSession,
        repo: AbstractEventRepository | None = None,
    ) -> None:
        self.session = session
        self.repo: AbstractEventRepository = repo or EventRepository(session)

    async def get(self, event_id: uuid.UUID) -> Event | None:
        return await self.repo.get(event_id)

    async def log(
        self,
        job_id: uuid.UUID,
        node: str,
        status: EventStatus = EventStatus.STARTED,
        payload: dict | None = None,
    ) -> Event:
        """Зафиксировать событие пайплайна."""
        event = await self.repo.create_event(
            job_id=job_id, node=node, status=status, payload_json=payload or {}
        )
        logger.debug("Событие: job={} node={} status={}", job_id, node, status.value)
        return event

    async def list_by_job(
        self, job_id: uuid.UUID, *, since=None, limit: int = 500
    ) -> list[Event]:
        """История событий джоба (для SSE/поллинга можно передавать since)."""
        return await self.repo.list_by_job(job_id, since=since, limit=limit)

    async def get_last_by_node(self, job_id: uuid.UUID, node: str) -> Event | None:
        return await self.repo.get_last_by_node(job_id, node)
