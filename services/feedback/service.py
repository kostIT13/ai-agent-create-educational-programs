import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.feedback import Feedback
from services.feedback.base import AbstractFeedbackRepository
from services.feedback.repository import FeedbackRepository

MIN_RATING = 1
MAX_RATING = 5


class FeedbackService:
    def __init__(
        self,
        session: AsyncSession,
        repo: AbstractFeedbackRepository | None = None,
    ) -> None:
        self.session = session
        self.repo: AbstractFeedbackRepository = repo or FeedbackRepository(session)

    async def get(self, feedback_id: uuid.UUID) -> Feedback | None:
        return await self.repo.get(feedback_id)

    async def add(
        self,
        course_id: uuid.UUID,
        entity_id: str,
        rating: int,
        *,
        comment: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> Feedback:
        """Добавить отзыв на сущность курса (узел графа и т.п.)."""
        if not MIN_RATING <= rating <= MAX_RATING:
            raise ValueError(f"Рейтинг должен быть от {MIN_RATING} до {MAX_RATING}")
        feedback = await self.repo.create(
            course_id=course_id,
            entity_id=entity_id,
            rating=rating,
            comment=comment,
            created_by=created_by,
        )
        logger.info(
            "Отзыв добавлен: course={} entity={} rating={}", course_id, entity_id, rating
        )
        return feedback

    async def list_by_course(self, course_id: uuid.UUID) -> list[Feedback]:
        return await self.repo.list_by_course(course_id)

    async def list_by_entity(self, course_id: uuid.UUID, entity_id: str) -> list[Feedback]:
        return await self.repo.list_by_entity(course_id, entity_id)

    async def avg_rating_by_entity(self, course_id: uuid.UUID) -> list[tuple[str, float, int]]:
        """Агрегированный рейтинг по сущностям курса (для брифа LLM)."""
        return await self.repo.avg_rating_by_entity(course_id)

    async def delete(self, feedback_id: uuid.UUID) -> bool:
        return await self.repo.delete_by_id(feedback_id)
