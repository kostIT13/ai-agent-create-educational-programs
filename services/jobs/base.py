import uuid
from abc import abstractmethod
from datetime import datetime

from database.models.jobs import Job, JobStatus
from services.base import AbstractRepository


class AbstractJobRepository(AbstractRepository[Job]):

    @abstractmethod
    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Job]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_status(
        self, status: JobStatus, *, limit: int = 100, offset: int = 0
    ) -> list[Job]:
        raise NotImplementedError

    @abstractmethod
    async def find_running_by_course(self, course_id: uuid.UUID) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def update_progress(self, job_id: uuid.UUID, progress: int) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_started(self, job_id: uuid.UUID, started_at: datetime) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_finished(
        self, job_id: uuid.UUID, status: JobStatus, finished_at: datetime
    ) -> Job | None:
        raise NotImplementedError
