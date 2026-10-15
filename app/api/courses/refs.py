"""Эндпоинты загрузки референсов курса (RAG, Этап 4).

POST /courses/{id}/refs — multipart-загрузка файлов (PDF/DOCX/PPTX/MD/TXT)
и/или URL; файлы парсятся, чанки эмбеддятся и пишутся в Qdrant.
GET /courses/{id}/refs — список загруженных референсов.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.api.courses.dependencies import CourseServiceDependency
from app.api.references.schemas import ReferenceRead
from app.api.references.dependencies import ReferenceServiceDependency
from rag.schemas import IngestResult


router = APIRouter(prefix="/courses", tags=["courses-refs"])


class RefsIngestResponse(BaseModel):
    """Результат загрузки референсов."""

    results: list[IngestResult] = Field(default_factory=list)
    total_chunks: int = 0


@router.post(
    "/{course_id}/refs",
    response_model=RefsIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_course_refs(
    course_id: uuid.UUID,
    service: ReferenceServiceDependency,
    course_service: CourseServiceDependency,
    files: Annotated[list[UploadFile], File()] = [],
    urls: Annotated[list[str], Form()] = [],
):
    """Загрузить референсы курса: файлы (multipart) и/или URL-список.

    Каждый файл парсится (Docling для PDF/DOCX/PPTX), чанки эмбеддятся
    и сохраняются в Qdrant (коллекция course_{id}_refs). В БД пишется
    запись Reference. Пустой результат (0 чанков) — не ошибка.
    """
    if not files and not urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Передайте хотя бы один файл или URL",
        )

    # Проверяем, что курс существует
    course = await course_service.get(course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден"
        )

    results: list[IngestResult] = []
    total = 0

    for upload in files:
        content = await upload.read()
        try:
            result = await service.ingest_file(
                course_id, upload.filename or "file", content
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc
        results.append(result)
        total += result.chunks_count

    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            result = await service.ingest_url(course_id, url)
        except Exception as exc:
            results.append(IngestResult(source=url, error=str(exc)))
            continue
        results.append(result)
        total += result.chunks_count

    return RefsIngestResponse(results=results, total_chunks=total)


@router.get("/{course_id}/refs", response_model=list[ReferenceRead])
async def list_course_refs(
    course_id: uuid.UUID,
    service: ReferenceServiceDependency,
    course_service: CourseServiceDependency,
):
    """Список загруженных референсов курса."""
    course = await course_service.get(course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден"
        )
    return await service.list_by_course(course_id)