import uuid
from datetime import datetime
from database.models.events import Event, EventStatus
from services.repository import SQLAlchemyRepository
from services.events.base import AbstractEventRepository


class EventRepository(AbstractEventRepository, SQLAlchemyRepository[Event]):
    model = Event

    async def list_by_job(
        self,
        job_id: uuid.UUID,
        *,
        since: datetime | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[Event]:
        conditions = [Event.job_id == job_id]
        if since is not None:
            conditions.append(Event.ts > since)
        return await self.find_many(
            *conditions, limit=limit, offset=offset, order_by=Event.ts
        )

    async def get_last_by_node(self, job_id: uuid.UUID, node: str) -> Event | None:
        events = await self.find_many(
            Event.job_id == job_id,
            Event.node == node,
            limit=1,
            order_by=Event.ts.desc(),
        )
        return events[0] if events else None

    async def create_event(
        self, job_id: uuid.UUID, node: str, status: EventStatus, payload_json: dict
    ) -> Event:
        return await self.create(
            job_id=job_id, node=node, status=status, payload_json=payload_json
        )
