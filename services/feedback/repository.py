import uuid
from sqlalchemy import func, select
from database.models.feedback import Feedback
from services.repository import SQLAlchemyRepository
from services.feedback.base import AbstractFeedbackRepository


class FeedbackRepository(AbstractFeedbackRepository, SQLAlchemyRepository[Feedback]):
    model = Feedback

    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Feedback]:
        return await self.find_many(
            Feedback.course_id == course_id,
            limit=limit,
            offset=offset,
            order_by=Feedback.created_at.desc(),
        )

    async def list_by_entity(
        self, course_id: uuid.UUID, entity_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[Feedback]:
        return await self.find_many(
            Feedback.course_id == course_id,
            Feedback.entity_id == entity_id,
            limit=limit,
            offset=offset,
            order_by=Feedback.created_at.desc(),
        )

    async def avg_rating_by_entity(self, course_id: uuid.UUID) -> list[tuple[str, float, int]]:
        stmt = (
            select(
                Feedback.entity_id,
                func.avg(Feedback.rating),
                func.count(),
            )
            .where(Feedback.course_id == course_id)
            .group_by(Feedback.entity_id)
        )
        result = await self.session.execute(stmt)
        return [
            (row.entity_id, float(row.avg or 0), int(row.count))
            for row in result.all()
        ]
