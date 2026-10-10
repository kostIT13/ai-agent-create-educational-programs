import uuid
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.jobs import Job, JobStatus
from services.jobs.base import AbstractJobRepository
from services.jobs.repository import JobRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


class JobService:
    def __init__(
        self,
        session: AsyncSession,
        repo: AbstractJobRepository | None = None,
    ) -> None:
        self.session = session
        self.repo: AbstractJobRepository = repo or JobRepository(session)

    async def get(self, job_id: uuid.UUID) -> Job | None:
        return await self.repo.get(job_id)

    async def get_or_raise(self, job_id: uuid.UUID) -> Job:
        job = await self.repo.get(job_id)
        if job is None:
            raise KeyError(f"Джоб с id={job_id} не найден")
        return job

    async def create(self, course_id: uuid.UUID) -> Job:
        """Поставить задачу генерации в очередь.

        Для одного курса одновременно может быть только одна активная задача.
        """
        running = await self.repo.find_running_by_course(course_id)
        if running is not None:
            raise ValueError(
                f"Для курса {course_id} уже есть активная задача {running.id} "
                f"в статусе {running.status.value}"
            )
        job = await self.repo.create(course_id=course_id, status=JobStatus.QUEUED)
        logger.info("Джоб создан: id={} course_id={}", job.id, course_id)
        return job

    async def list_by_course(self, course_id: uuid.UUID) -> list[Job]:
        return await self.repo.list_by_course(course_id)

    async def list_by_status(self, status: JobStatus) -> list[Job]:
        return await self.repo.list_by_status(status)

    async def start(self, job_id: uuid.UUID) -> Job:
        job = await self.get_or_raise(job_id)
        if job.status is not JobStatus.QUEUED:
            raise ValueError(f"Джоб {job_id} нельзя запустить из статуса {job.status.value}")
        return await self.repo.mark_started(job_id, _now())

    async def set_progress(self, job_id: uuid.UUID, progress: int) -> Job | None:
        return await self.repo.update_progress(job_id, progress)

    async def complete(self, job_id: uuid.UUID) -> Job:
        job = await self.get_or_raise(job_id)
        if job.status is not JobStatus.RUNNING:
            raise ValueError(f"Джоб {job_id} нельзя завершить из статуса {job.status.value}")
        return await self.repo.mark_finished(job_id, JobStatus.COMPLETED, _now())

    async def fail(self, job_id: uuid.UUID, error: str) -> Job:
        job = await self.get_or_raise(job_id)
        if job.status not in (JobStatus.QUEUED, JobStatus.RUNNING):
            raise ValueError(f"Джоб {job_id} нельзя зафейлить из статуса {job.status.value}")
        updated = await self.repo.update_by_id(job_id, error=error)
        return await self.repo.mark_finished(job_id, JobStatus.FAILED, _now()) if updated else job

    async def cancel(self, job_id: uuid.UUID) -> Job:
        job = await self.get_or_raise(job_id)
        if job.status not in (JobStatus.QUEUED, JobStatus.RUNNING):
            raise ValueError(f"Джоб {job_id} нельзя отменить из статуса {job.status.value}")
        return await self.repo.mark_finished(job_id, JobStatus.CANCELLED, _now())

    async def delete(self, job_id: uuid.UUID) -> bool:
        return await self.repo.delete_by_id(job_id)
