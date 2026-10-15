"""Qdrant-хранилище референсов курса.

Коллекция: `{prefix}_{course_id}_refs` — изоляция референсов разных курсов.
Фаза 1 (MVP): dense-векторы, поиск по косинусной близости.
"""

import uuid
from typing import Any

from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from core.configs.rag_config import rag_settings
from rag.schemas import Chunk, RetrievedChunk


def collection_name(course_id: uuid.UUID) -> str:
    return f"{rag_settings.COLLECTION_PREFIX}_{course_id}_refs"


def chunk_full_id(course_id: uuid.UUID, chunk_id: str) -> str:
    """Полный id чанка: `course_{course_id}_refs:{chunk_id}` — попадает в source_refs."""
    return f"{collection_name(course_id)}:{chunk_id}"


def _point_id(full_id: str) -> str:
    """Стабильный uuid из полного id чанка (для point id в Qdrant)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, full_id))


class QdrantStore:
    """Тонкая обёртка над Qdrant для коллекций референсов курса."""

    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        self._client = AsyncQdrantClient(
            url=url or rag_settings.QDRANT_URL,
            api_key=api_key or rag_settings.QDRANT_API_KEY or None,
        )

    async def ensure_collection(self, course_id: uuid.UUID) -> None:
        """Создать коллекцию курса, если её нет."""
        name = collection_name(course_id)
        existing = await self._client.get_collections()
        if any(c.name == name for c in existing.collections):
            return
        await self._client.create_collection(
            collection_name=name,
            vectors_config=qm.VectorParams(
                size=rag_settings.EMBEDDINGS_DIM,
                distance=qm.Distance.COSINE,
            ),
        )
        logger.info("Коллекция Qdrant создана: {}", name)

    async def upsert_chunks(
        self,
        course_id: uuid.UUID,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> list[str]:
        """Записать чанки с векторами; возвращает полные id чанков."""
        if not chunks:
            return []
        name = collection_name(course_id)
        await self.ensure_collection(course_id)

        points: list[qm.PointStruct] = []
        full_ids: list[str] = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            full_id = chunk_full_id(course_id, f"{uuid.uuid4().hex[:12]}")
            full_ids.append(full_id)
            points.append(
                qm.PointStruct(
                    id=_point_id(full_id),
                    vector=vector,
                    payload={
                        "chunk_id": full_id,
                        "text": chunk.text,
                        "file": chunk.file,
                        "section": chunk.section,
                        "page": chunk.page,
                        "source_type": chunk.source_type,
                        "date": chunk.date,
                    },
                )
            )
        await self._client.upsert(collection_name=name, points=points)
        logger.info("Upsert в Qdrant: collection={} points={}", name, len(points))
        return full_ids

    async def search(
        self,
        course_id: uuid.UUID,
        query_vector: list[float],
        *,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Dense-поиск по коллекции курса."""
        name = collection_name(course_id)
        k = top_k or rag_settings.TOP_K
        try:
            hits = await self._client.search(
                collection_name=name,
                query_vector=query_vector,
                limit=k,
                score_threshold=rag_settings.SCORE_THRESHOLD or None,
            )
        except Exception as exc:
            logger.warning("Поиск в Qdrant не удался (collection={}): {}", name, exc)
            return []

        results: list[RetrievedChunk] = []
        for hit in hits:
            payload: dict[str, Any] = hit.payload or {}
            results.append(
                RetrievedChunk(
                    chunk_id=payload.get("chunk_id", ""),
                    text=payload.get("text", ""),
                    score=float(hit.score),
                    metadata={
                        "file": payload.get("file", ""),
                        "section": payload.get("section", ""),
                        "page": payload.get("page"),
                        "source_type": payload.get("source_type", ""),
                        "date": payload.get("date"),
                    },
                )
            )
        return results

    async def chunk_exists(self, course_id: uuid.UUID, chunk_id: str) -> bool:
        """Существует ли чанк с полным id (для Critic — детерминированная проверка)."""
        name = collection_name(course_id)
        try:
            point = await self._client.retrieve(
                collection_name=name,
                ids=[_point_id(chunk_id)],
                with_vectors=False,
            )
            return len(point) > 0
        except Exception:
            return False

    async def count(self, course_id: uuid.UUID) -> int:
        name = collection_name(course_id)
        try:
            info = await self._client.get_collection(collection_name=name)
            return int(info.points_count or 0)
        except Exception:
            return 0

    async def delete_collection(self, course_id: uuid.UUID) -> None:
        name = collection_name(course_id)
        try:
            await self._client.delete_collection(collection_name=name)
            logger.info("Коллекция Qdrant удалена: {}", name)
        except Exception as exc:
            logger.warning("Не удалось удалить коллекцию {}: {}", name, exc)


_store: QdrantStore | None = None


def get_store() -> QdrantStore:
    global _store
    if _store is None:
        _store = QdrantStore()
    return _store