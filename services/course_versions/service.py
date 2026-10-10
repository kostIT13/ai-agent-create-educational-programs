import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.course_versions import CourseVersion
from services.course_versions.base import AbstractCourseVersionRepository
from services.course_versions.repository import CourseVersionRepository


class CourseVersionService:
    def __init__(
        self,
        session: AsyncSession,
        repo: AbstractCourseVersionRepository | None = None,
    ) -> None:
        self.session = session
        self.repo: AbstractCourseVersionRepository = repo or CourseVersionRepository(session)

    async def get(self, version_id: uuid.UUID) -> CourseVersion | None:
        return await self.repo.get(version_id)

    async def get_or_raise(self, version_id: uuid.UUID) -> CourseVersion:
        obj = await self.repo.get(version_id)
        if obj is None:
            raise KeyError(f"Версия курса с id={version_id} не найдена")
        return obj

    async def list_by_course(self, course_id: uuid.UUID) -> list[CourseVersion]:
        return await self.repo.list_by_course(course_id)

    async def get_latest(self, course_id: uuid.UUID) -> CourseVersion | None:
        return await self.repo.get_latest(course_id)

    async def get_by_number(self, course_id: uuid.UUID, version: int) -> CourseVersion | None:
        return await self.repo.get_by_number(course_id, version)

    async def create_next_version(
        self,
        course_id: uuid.UUID,
        graph_json: dict,
        *,
        diff_json: dict | None = None,
    ) -> CourseVersion:
        """Создать следующую версию графа курса (version = последняя + 1)."""
        latest = await self.repo.get_latest(course_id)
        next_version = (latest.version + 1) if latest else 1
        obj = await self.repo.create(
            course_id=course_id,
            version=next_version,
            graph_json=graph_json,
            diff_json=diff_json,
        )
        logger.info("Создана версия {} курса {}", next_version, course_id)
        return obj
