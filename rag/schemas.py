from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Чанк документа с метаданными (до эмбеддинга)."""

    text: str = Field(..., min_length=1)
    file: str = Field(..., description="Имя файла или URL источника")
    section: str = Field(default="", description="Заголовок раздела, из которого взят чанк")
    page: int | None = Field(default=None)
    source_type: str = Field(
        default="document",
        description="Тип источника: standard/program/article/blog/forum/document",
    )
    date: str | None = Field(default=None, description="Дата источника, если известна")


class RetrievedChunk(BaseModel):

    chunk_id: str
    text: str
    score: float = 0.0
    metadata: dict = Field(default_factory=dict)


class IngestResult(BaseModel):
    """Результат ингеста одного файла/URL."""

    source: str = Field(..., description="Имя файла или URL")
    chunks_count: int = 0
    chunk_ids: list[str] = Field(default_factory=list)
    error: str | None = None