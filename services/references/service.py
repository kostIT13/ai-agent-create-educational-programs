import mimetypes
import uuid
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.references import Reference
from rag.ingest import parse_to_chunks, parse_url_to_chunks
from rag.retriever import ingest_chunks_for_course
from rag.schemas import IngestResult
from services.references.base import AbstractReferenceRepository
from services.references.repository import ReferenceRepository


def _guess_mime(filename: str) -> str:
    """MIME-тип по расширению файла."""
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


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

    async def ingest_file(
        self,
        course_id: uuid.UUID,
        filename: str,
        content: bytes,
        *,
        source_type: str | None = None,
    ) -> IngestResult:
        """Загрузить файл: чанки → эмбеддинги → Qdrant + запись в БД.

        Бизнес-логика ингеста живёт здесь (общий слой для REST и MCP).
        """
        chunks = parse_to_chunks(content, filename, source_type=source_type)
        if not chunks:
            return IngestResult(source=filename, chunks_count=0)

        chunk_ids = await ingest_chunks_for_course(course_id, chunks)
        s3_key = f"course_{course_id}/refs/{filename}"
        await self.add(course_id, filename, s3_key, mime=_guess_mime(filename))
        logger.info(
            "Референс загружен: course={} file={!r} chunks={}",
            course_id,
            filename,
            len(chunk_ids),
        )
        return IngestResult(
            source=filename, chunks_count=len(chunk_ids), chunk_ids=chunk_ids
        )

    async def ingest_url(self, course_id: uuid.UUID, url: str) -> IngestResult:
        """Загрузить URL: скачать → чанки → эмбеддинги → Qdrant + запись в БД."""
        chunks = parse_url_to_chunks(url)
        if not chunks:
            return IngestResult(source=url, chunks_count=0)

        chunk_ids = await ingest_chunks_for_course(course_id, chunks)
        s3_key = f"course_{course_id}/refs/{url}"
        await self.add(course_id, url, s3_key, mime="text/html")
        logger.info(
            "Референс загружен: course={} url={!r} chunks={}",
            course_id,
            url,
            len(chunk_ids),
        )
        return IngestResult(
            source=url, chunks_count=len(chunk_ids), chunk_ids=chunk_ids
        )
