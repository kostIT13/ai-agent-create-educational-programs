import uuid
from abc import abstractmethod
from database.models.courses import Course, CourseStatus
from services.base import AbstractRepository


class AbstractCourseRepository(AbstractRepository[Course]):

    @abstractmethod
    async def list_by_creator(
        self, created_by: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Course]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_status(
        self, status: CourseStatus, *, limit: int = 100, offset: int = 0
    ) -> list[Course]:
        raise NotImplementedError
