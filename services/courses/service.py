import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.courses import Course, CourseStatus
from services.courses.base import AbstractCourseRepository
from services.courses.repository import CourseRepository

STATUS_TRANSITIONS: dict[CourseStatus, set[CourseStatus]] = {
    CourseStatus.DRAFT: {CourseStatus.PROCESSING, CourseStatus.ARCHIVED},
    CourseStatus.PROCESSING: {CourseStatus.READY, CourseStatus.FAILED, CourseStatus.ARCHIVED},
    CourseStatus.READY: {CourseStatus.PROCESSING, CourseStatus.ARCHIVED},
    CourseStatus.FAILED: {CourseStatus.PROCESSING, CourseStatus.ARCHIVED},
    CourseStatus.ARCHIVED: set(),
}


class CourseService:
    def __init__(
        self,
        session: AsyncSession,
        repo: AbstractCourseRepository | None = None,
    ) -> None:
        self.session = session
        self.repo: AbstractCourseRepository = repo or CourseRepository(session)

    async def get(self, course_id: uuid.UUID) -> Course | None:
        return await self.repo.get(course_id)

    async def get_or_raise(self, course_id: uuid.UUID) -> Course:
        course = await self.repo.get(course_id)
        if course is None:
            raise KeyError(f"Курс с id={course_id} не найден")
        return course

    async def create(
        self,
        title: str,
        *,
        brief_json: dict | None = None,
        created_by: uuid.UUID | None = None,
    ) -> Course:
        course = await self.repo.create(
            title=title,
            brief_json=brief_json or {},
            created_by=created_by,
            status=CourseStatus.DRAFT,
        )
        logger.info("Курс создан: id={} title={!r}", course.id, course.title)
        return course

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[Course]:
        return await self.repo.find_many(
            limit=limit, offset=offset, order_by=Course.updated_at.desc()
        )

    async def list_by_creator(self, created_by: uuid.UUID) -> list[Course]:
        return await self.repo.list_by_creator(created_by)

    async def list_by_status(self, status: CourseStatus) -> list[Course]:
        return await self.repo.list_by_status(status)

    async def change_status(self, course_id: uuid.UUID, new_status: CourseStatus) -> Course:
        """Перевести курс в новый статус с проверкой допустимого перехода."""
        course = await self.get_or_raise(course_id)
        allowed = STATUS_TRANSITIONS.get(course.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Недопустимый переход статуса курса {course_id}: "
                f"{course.status.value} -> {new_status.value}. Разрешено: "
                f"{sorted(s.value for s in allowed) or 'ничего'}"
            )
        course = await self.repo.update(course, status=new_status)
        logger.info("Статус курса {}: {} -> {}", course_id, course.status, new_status)
        return course

    async def update_fields(self, course_id: uuid.UUID, **fields) -> Course:
        """Обновить произвольные поля курса (title, brief_json)."""
        course = await self.get_or_raise(course_id)
        return await self.repo.update(course, **fields)

    async def update_brief(self, course_id: uuid.UUID, brief_json: dict) -> Course:
        return await self.update_fields(course_id, brief_json=brief_json)

    async def archive(self, course_id: uuid.UUID) -> Course:
        return await self.change_status(course_id, CourseStatus.ARCHIVED)

    async def delete(self, course_id: uuid.UUID) -> bool:
        return await self.repo.delete_by_id(course_id)
