import uuid
from datetime import datetime
from database.models.jobs import Job, JobStatus
from services.repository import SQLAlchemyRepository
from services.jobs.base import AbstractJobRepository


class JobRepository(AbstractJobRepository, SQLAlchemyRepository[Job]):
    model = Job

    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Job]:
        return await self.find_many(
            Job.course_id == course_id,
            limit=limit,
            offset=offset,
            order_by=Job.created_at.desc(),
        )

    async def list_by_status(
        self, status: JobStatus, *, limit: int = 100, offset: int = 0
    ) -> list[Job]:
        return await self.find_many(
            Job.status == status,
            limit=limit,
            offset=offset,
            order_by=Job.created_at.desc(),
        )

    async def find_running_by_course(self, course_id: uuid.UUID) -> Job | None:
        return await self.find_one(
            Job.course_id == course_id,
            Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
        )

    async def update_progress(self, job_id: uuid.UUID, progress: int) -> Job | None:
        return await self.update_by_id(job_id, progress=max(0, min(progress, 100)))

    async def mark_started(self, job_id: uuid.UUID, started_at: datetime) -> Job | None:
        return await self.update_by_id(job_id, status=JobStatus.RUNNING, started_at=started_at)

    async def mark_finished(
        self, job_id: uuid.UUID, status: JobStatus, finished_at: datetime
    ) -> Job | None:
        data: dict = {"status": status, "finished_at": finished_at}
        if status == JobStatus.COMPLETED:
            data["progress"] = 100
        return await self.update_by_id(job_id, **data)
