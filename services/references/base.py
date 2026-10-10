import uuid
from abc import abstractmethod
from database.models.references import Reference
from services.base import AbstractRepository


class AbstractReferenceRepository(AbstractRepository[Reference]):

    @abstractmethod
    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Reference]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_s3_key(self, course_id: uuid.UUID, s3_key: str) -> Reference | None:
        raise NotImplementedError
