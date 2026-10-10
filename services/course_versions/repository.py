import uuid
from sqlalchemy import select
from database.models.course_versions import CourseVersion
from services.repository import SQLAlchemyRepository
from services.course_versions.base import AbstractCourseVersionRepository


class CourseVersionRepository(
    AbstractCourseVersionRepository, SQLAlchemyRepository[CourseVersion]
):
    model = CourseVersion

    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[CourseVersion]:
        return await self.find_many(
            CourseVersion.course_id == course_id,
            limit=limit,
            offset=offset,
            order_by=CourseVersion.version.desc(),
        )

    async def get_latest(self, course_id: uuid.UUID) -> CourseVersion | None:
        stmt = (
            select(CourseVersion)
            .where(CourseVersion.course_id == course_id)
            .order_by(CourseVersion.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_number(self, course_id: uuid.UUID, version: int) -> CourseVersion | None:
        return await self.find_one(
            CourseVersion.course_id == course_id,
            CourseVersion.version == version,
        )
