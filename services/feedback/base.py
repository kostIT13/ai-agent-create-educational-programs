import uuid
from abc import abstractmethod
from database.models.feedback import Feedback
from services.base import AbstractRepository


class AbstractFeedbackRepository(AbstractRepository[Feedback]):

    @abstractmethod
    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Feedback]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_entity(
        self, course_id: uuid.UUID, entity_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[Feedback]:
        raise NotImplementedError

    @abstractmethod
    async def avg_rating_by_entity(self, course_id: uuid.UUID) -> list[tuple[str, float, int]]:
        """Средний рейтинг по сущностям курса: [(entity_id, avg, count), ...]."""
        raise NotImplementedError
