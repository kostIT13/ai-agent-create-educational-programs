import uuid
from loguru import logger
from rag.embeddings import EmbeddingsClient, get_embeddings_client
from rag.schemas import Chunk, RetrievedChunk
from rag.store import QdrantStore, get_store


class Retriever:
    """Поиск по коллекции референсов курса."""

    def __init__(
        self,
        course_id: uuid.UUID,
        store: QdrantStore | None = None,
        embeddings: EmbeddingsClient | None = None,
    ) -> None:
        self.course_id = course_id
        self._store = store or get_store()
        self._embeddings = embeddings or get_embeddings_client()

    async def search(self, query: str, top_k: int = 6) -> list[RetrievedChunk]:
        """Гибридный поиск + реранк (в Фазе 1 — только dense)."""
        if not query.strip():
            return []
        try:
            vector = await self._embeddings.embed_one(query)
        except Exception as exc:
            logger.warning("Эмбеддинг запроса не удался: {}", exc)
            return []
        return await self._store.search(self.course_id, vector, top_k=top_k)

    def to_source_block(self, chunks: list[RetrievedChunk]) -> str:
        """Чанки → `<source id="...">...</source>` для вставки в промпт."""
        if not chunks:
            return ""
        parts = [
            f'<source id="{c.chunk_id}">\n{c.text}\n</source>' for c in chunks
        ]
        return "\n\n".join(parts)

    async def chunk_exists(self, chunk_id: str) -> bool:
        """Проверка валидности source_ref (для Critic)."""
        return await self._store.chunk_exists(self.course_id, chunk_id)

    async def count(self) -> int:
        return await self._store.count(self.course_id)


async def ingest_chunks_for_course(
    course_id: uuid.UUID,
    chunks: list[Chunk],
    *,
    store: QdrantStore | None = None,
    embeddings: EmbeddingsClient | None = None,
) -> list[str]:
    """Полный конвейер ингеста: чанки → эмбеддинги → Qdrant.

    Возвращает полные id записанных чанков (для source_refs).
    """
    if not chunks:
        return []
    store = store or get_store()
    embeddings = embeddings or get_embeddings_client()
    vectors = await embeddings.embed([c.text for c in chunks])
    return await store.upsert_chunks(course_id, chunks, vectors)