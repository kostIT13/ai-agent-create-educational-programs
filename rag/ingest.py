"""Ingest: файл/URL → markdown → структурные чанки.

- PDF/DOCX/PPTX — Docling (структурированный markdown: заголовки, таблицы, списки);
- MD/TXT — читаем как есть;
- URL — скачиваем через httpx и обрабатываем по Content-Type.

Docling импортируется лениво: если пакет не установлен, для бинарных форматов
возвращается понятная ошибка (текстовые форматы работают без Docling).
"""

import io
import mimetypes
import uuid
from pathlib import Path

import httpx
from loguru import logger

from core.configs.rag_config import rag_settings
from rag.chunking import chunk_markdown
from rag.schemas import Chunk, IngestResult

# Расширения, которые умеем читать без Docling
_TEXT_EXTENSIONS = {".md", ".txt", ".markdown"}


def _detect_source_type(name: str) -> str:
    """Грубая эвристика типа источника по имени файла."""
    lower = name.lower()
    if any(k in lower for k in ("фгос", "стандарт", "standard", "профстандарт", "esco", "digcomp")):
        return "standard"
    if any(k in lower for k in ("программа", "program", "учебный план", "syllabus", "курс")):
        return "program"
    if any(k in lower for k in ("статья", "article", "paper", "блог", "blog")):
        return "article"
    return "document"


def _docling_to_markdown(content: bytes, filename: str) -> str:
    """Конвертация бинарного документа в markdown через Docling."""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Docling не установлен. Установите `docling` для парсинга PDF/DOCX/PPTX "
            "или загрузите файл в формате MD/TXT."
        ) from exc

    converter = DocumentConverter()
    result = converter.convert(io.BytesIO(content))
    return result.document.export_to_markdown()


def _parse_bytes(content: bytes, filename: str) -> str:
    """Файл → markdown (Docling для бинарных, как есть для текстовых)."""
    ext = Path(filename).suffix.lower()
    if ext in _TEXT_EXTENSIONS:
        return content.decode("utf-8", errors="replace")
    return _docling_to_markdown(content, filename)


def _validate_file(filename: str, content: bytes) -> None:
    """Проверка расширения и размера файла."""
    ext = Path(filename).suffix.lower()
    if ext not in rag_settings.ALLOWED_EXT:
        raise ValueError(
            f"Недопустимый тип файла {ext!r}. Разрешены: {', '.join(rag_settings.ALLOWED_EXT)}"
        )
    size_mb = len(content) / (1024 * 1024)
    if size_mb > rag_settings.MAX_FILE_SIZE_MB:
        raise ValueError(
            f"Файл {filename!r} слишком большой: {size_mb:.1f} МБ "
            f"(лимит {rag_settings.MAX_FILE_SIZE_MB} МБ)"
        )


def ingest_bytes(
    content: bytes,
    filename: str,
    *,
    source_type: str | None = None,
    date: str | None = None,
) -> IngestResult:
    """Синхронный ингест: байты файла → чанки (без эмбеддинга и Qdrant).

    Возвращает IngestResult с текстами чанков; эмбеддинг и запись в Qdrant
    выполняет вызывающий код (см. rag/store.py).
    """
    _validate_file(filename, content)
    try:
        markdown = _parse_bytes(content, filename)
    except Exception as exc:
        logger.warning("Парсинг файла {!r} не удался: {}", filename, exc)
        return IngestResult(source=filename, error=str(exc))

    chunks = chunk_markdown(
        markdown,
        file=filename,
        source_type=source_type or _detect_source_type(filename),
        date=date,
    )
    return IngestResult(source=filename, chunks_count=len(chunks))


def ingest_url(url: str, *, timeout: float = 30.0) -> IngestResult:
    """Скачать URL и разобрать как документ."""
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=timeout)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Не удалось скачать URL {!r}: {}", url, exc)
        return IngestResult(source=url, error=str(exc))

    content_type = resp.headers.get("content-type", "")
    guessed = mimetypes.guess_extension(content_type.split(";")[0]) or ""
    filename = f"url_{uuid.uuid4().hex[:8]}{guessed}"
    return ingest_bytes(resp.content, filename, source_type="article")


def parse_to_chunks(
    content: bytes,
    filename: str,
    *,
    source_type: str | None = None,
    date: str | None = None,
) -> list[Chunk]:
    """Байты файла → список Chunk (полный конвейер без эмбеддинга)."""
    _validate_file(filename, content)
    markdown = _parse_bytes(content, filename)
    return chunk_markdown(
        markdown,
        file=filename,
        source_type=source_type or _detect_source_type(filename),
        date=date,
    )


def parse_url_to_chunks(url: str, *, timeout: float = 30.0) -> list[Chunk]:
    """URL → список Chunk."""
    resp = httpx.get(url, follow_redirects=True, timeout=timeout)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "")
    guessed = mimetypes.guess_extension(content_type.split(";")[0]) or ""
    filename = f"url_{uuid.uuid4().hex[:8]}{guessed}"
    return parse_to_chunks(resp.content, filename, source_type="article")