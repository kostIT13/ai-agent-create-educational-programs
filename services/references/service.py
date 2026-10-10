import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.references import Reference
from services.references.base import AbstractReferenceRepository
from services.references.repository import ReferenceRepository


class ReferenceService:
    def __init__(
        self,
        session: AsyncSession,
        repo: AbstractReferenceRepository | None = None,
    ) -> None:
        self.session = session
        self.repo: AbstractReferenceRepository = repo or ReferenceRepository(session)

    async def get(self, reference_id: uuid.UUID) -> Reference | None:
        return await self.repo.get(reference_id)

    async def get_or_raise(self, reference_id: uuid.UUID) -> Reference:
        obj = await self.repo.get(reference_id)
        if obj is None:
            raise KeyError(f"Справочник с id={reference_id} не найден")
        return obj

    async def add(
        self,
        course_id: uuid.UUID,
        name: str,
        s3_key: str,
        *,
        mime: str | None = None,
    ) -> Reference:
        """Зарегистрировать загруженный в S3 справочник."""
        if await self.repo.get_by_s3_key(course_id, s3_key):
            raise ValueError(
                f"Справочник с s3_key={s3_key!r} уже существует у курса {course_id}"
            )
        obj = await self.repo.create(course_id=course_id, name=name, s3_key=s3_key, mime=mime)
        logger.info("Справочник добавлен: id={} course={} name={!r}", obj.id, course_id, name)
        return obj

    async def list_by_course(self, course_id: uuid.UUID) -> list[Reference]:
        return await self.repo.list_by_course(course_id)

    async def delete(self, reference_id: uuid.UUID) -> bool:
        return await self.repo.delete_by_id(reference_id)
