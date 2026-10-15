from pydantic_settings import BaseSettings, SettingsConfigDict


class RAGSettings(BaseSettings):
    """Настройки RAG-контура (Этап 4).

    Фаза 1 (MVP): dense-only поиск. Эмбеддинги — через OpenAI API
    (text-embedding-3-large) либо локальный провайдер (bge-m3), если задан
    EMBEDDINGS_BASE_URL на совместимый OpenAI endpoint.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RAG_",
        extra="ignore",
    )

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    COLLECTION_PREFIX: str = "course"  # коллекция: {prefix}_{course_id}_refs

    # Эмбеддинги
    EMBEDDINGS_PROVIDER: str = "openai"  # openai | local
    EMBEDDINGS_MODEL: str = "text-embedding-3-large"
    EMBEDDINGS_BASE_URL: str = ""  # для локального OpenAI-совместимого endpoint
    EMBEDDINGS_API_KEY: str = ""
    EMBEDDINGS_DIM: int = 1024  # text-embedding-3-large по умолчанию 3072; 1024 — дешевле
    EMBEDDINGS_BATCH_SIZE: int = 32

    # Поиск
    TOP_K: int = 6
    SCORE_THRESHOLD: float = 0.0  # 0 = не фильтровать по порогу

    # Ingest
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_MIME: tuple[str, ...] = (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/markdown",
        "text/plain",
    )
    ALLOWED_EXT: tuple[str, ...] = (".pdf", ".docx", ".pptx", ".md", ".txt")
    MAX_CHUNK_CHARS: int = 2000
    MIN_CHUNK_CHARS: int = 30


rag_settings = RAGSettings()