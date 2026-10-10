import uuid
from abc import abstractmethod
from datetime import datetime
from database.models.events import Event, EventStatus
from services.base import AbstractRepository


class AbstractEventRepository(AbstractRepository[Event]):

    @abstractmethod
    async def list_by_job(
        self,
        job_id: uuid.UUID,
        *,
        since: datetime | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[Event]:
        raise NotImplementedError

    @abstractmethod
    async def get_last_by_node(self, job_id: uuid.UUID, node: str) -> Event | None:
        raise NotImplementedError

    @abstractmethod
    async def create_event(
        self, job_id: uuid.UUID, node: str, status: EventStatus, payload_json: dict
    ) -> Event:
        raise NotImplementedError
