import uuid
from database.models.references import Reference
from services.repository import SQLAlchemyRepository
from services.references.base import AbstractReferenceRepository


class ReferenceRepository(AbstractReferenceRepository, SQLAlchemyRepository[Reference]):
    model = Reference

    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[Reference]:
        return await self.find_many(
            Reference.course_id == course_id,
            limit=limit,
            offset=offset,
            order_by=Reference.created_at.desc(),
        )

    async def get_by_s3_key(self, course_id: uuid.UUID, s3_key: str) -> Reference | None:
        return await self.find_one(
            Reference.course_id == course_id,
            Reference.s3_key == s3_key,
        )
