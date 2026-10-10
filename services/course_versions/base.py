import uuid
from abc import abstractmethod
from database.models.course_versions import CourseVersion
from services.base import AbstractRepository


class AbstractCourseVersionRepository(AbstractRepository[CourseVersion]):

    @abstractmethod
    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[CourseVersion]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest(self, course_id: uuid.UUID) -> CourseVersion | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_number(self, course_id: uuid.UUID, version: int) -> CourseVersion | None:
        raise NotImplementedError
