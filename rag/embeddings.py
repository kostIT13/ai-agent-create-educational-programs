from loguru import logger
from openai import AsyncOpenAI
from core.configs.rag_config import rag_settings


class EmbeddingsError(RuntimeError):
    """Не удалось получить эмбеддинги."""


class EmbeddingsClient:
    """Клиент эмбеддингов (dense)."""

    def __init__(self) -> None:
        base_url = rag_settings.EMBEDDINGS_BASE_URL or None
        api_key = rag_settings.EMBEDDINGS_API_KEY or "EMPTY"
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = rag_settings.EMBEDDINGS_MODEL
        self.dim = rag_settings.EMBEDDINGS_DIM
        logger.info(
            "Embeddings client: model={} dim={} base_url={}",
            self.model,
            self.dim,
            base_url or "openai",
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Векторизовать список текстов (батчами)."""
        if not texts:
            return []
        vectors: list[list[float]] = []
        batch_size = rag_settings.EMBEDDINGS_BATCH_SIZE
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            try:
                resp = await self._client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dim,
                )
            except Exception as exc:
                raise EmbeddingsError(
                    f"Ошибка эмбеддингов (model={self.model}): {exc}"
                ) from exc
            vectors.extend([item.embedding for item in resp.data])
        return vectors

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed([text])
        return vectors[0]


_embeddings: EmbeddingsClient | None = None


def get_embeddings_client() -> EmbeddingsClient:
    global _embeddings
    if _embeddings is None:
        _embeddings = EmbeddingsClient()
    return _embeddings