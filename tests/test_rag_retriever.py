"""Offline-тесты ретривера: search, to_source_block, chunk_exists, режим без референсов."""

import uuid

import pytest

from rag.retriever import Retriever, ingest_chunks_for_course
from rag.schemas import Chunk, RetrievedChunk


class FakeStore:
    """Имитация QdrantStore без сети."""

    def __init__(self) -> None:
        self.chunks: dict[str, RetrievedChunk] = {}
        self.search_calls: list[str] = []

    async def search(self, course_id, query_vector, *, top_k=6):
        self.search_calls.append(str(course_id))
        return list(self.chunks.values())[:top_k]

    async def chunk_exists(self, course_id, chunk_id: str) -> bool:
        return chunk_id in self.chunks

    async def count(self, course_id) -> int:
        return len(self.chunks)

    async def upsert_chunks(self, course_id, chunks, vectors):
        ids = []
        for i, chunk in enumerate(chunks):
            full_id = f"course_{course_id}_refs:chunk{i}"
            ids.append(full_id)
            self.chunks[full_id] = RetrievedChunk(
                chunk_id=full_id,
                text=chunk.text,
                score=0.9,
                metadata={"file": chunk.file, "section": chunk.section},
            )
        return ids


class FakeEmbeddings:
    """Имитация эмбеддингов: детерминированный вектор по длине текста."""

    async def embed(self, texts):
        return [[float(len(t))] * 4 for t in texts]

    async def embed_one(self, text):
        return [float(len(text))] * 4


@pytest.fixture
def course_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def retriever(course_id) -> Retriever:
    return Retriever(
        course_id,
        store=FakeStore(),
        embeddings=FakeEmbeddings(),
    )


@pytest.mark.asyncio
async def test_search_returns_chunks(retriever: Retriever) -> None:
    store = retriever._store
    await store.upsert_chunks(
        retriever.course_id,
        [Chunk(text="Требования к выпускнику: умеет X", file="std.md")],
        [[0.1, 0.2, 0.3, 0.4]],
    )
    results = await retriever.search("требования к выпускнику")
    assert len(results) == 1
    assert results[0].chunk_id.startswith(f"course_{retriever.course_id}_refs:")


@pytest.mark.asyncio
async def test_search_empty_without_refs(retriever: Retriever) -> None:
    """Режим «без референсов»: пустой результат, не ошибка."""
    results = await retriever.search("любой запрос")
    assert results == []


def test_to_source_block(retriever: Retriever) -> None:
    chunks = [
        RetrievedChunk(
            chunk_id="course_abc_refs:42",
            text="Текст чанка",
            score=0.9,
            metadata={"file": "std.md"},
        )
    ]
    block = retriever.to_source_block(chunks)
    assert '<source id="course_abc_refs:42">' in block
    assert "Текст чанка" in block
    assert "</source>" in block


def test_to_source_block_empty(retriever: Retriever) -> None:
    assert retriever.to_source_block([]) == ""


@pytest.mark.asyncio
async def test_chunk_exists(retriever: Retriever) -> None:
    store = retriever._store
    await store.upsert_chunks(
        retriever.course_id,
        [Chunk(text="Чанк", file="a.md")],
        [[0.1, 0.2, 0.3, 0.4]],
    )
    existing = next(iter(store.chunks))
    assert await retriever.chunk_exists(existing) is True
    assert await retriever.chunk_exists("course_x_refs:nope") is False


@pytest.mark.asyncio
async def test_ingest_chunks_for_course(course_id: uuid.UUID) -> None:
    store = FakeStore()
    chunks = [Chunk(text="Первый чанк", file="a.md"), Chunk(text="Второй чанк", file="a.md")]
    ids = await ingest_chunks_for_course(
        course_id, chunks, store=store, embeddings=FakeEmbeddings()
    )
    assert len(ids) == 2
    assert all(i.startswith(f"course_{course_id}_refs:") for i in ids)
    assert await store.count(course_id) == 2


@pytest.mark.asyncio
async def test_ingest_empty_chunks(course_id: uuid.UUID) -> None:
    store = FakeStore()
    ids = await ingest_chunks_for_course(course_id, [], store=store, embeddings=FakeEmbeddings())
    assert ids == []