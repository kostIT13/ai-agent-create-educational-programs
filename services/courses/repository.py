import uuid
from database.models.courses import Course, CourseStatus
from services.repository import SQLAlchemyRepository
from services.courses.base import AbstractCourseRepository


class CourseRepository(AbstractCourseRepository, SQLAlchemyRepository[Course]):
    model = Course

    async def list_by_creator(
        self, created_by: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Course]:
        return await self.find_many(
            Course.created_by == created_by,
            limit=limit,
            offset=offset,
            order_by=Course.updated_at.desc(),
        )

    async def list_by_status(
        self, status: CourseStatus, *, limit: int = 100, offset: int = 0
    ) -> list[Course]:
        return await self.find_many(
            Course.status == status,
            limit=limit,
            offset=offset,
            order_by=Course.updated_at.desc(),
        )
