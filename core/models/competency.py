import enum
from pydantic import BaseModel, Field


class BloomLevel(str, enum.Enum):
    """Уровни таксономии Блума."""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class Competency(BaseModel):
    """Компетенция курса."""

    id: str = Field(..., pattern=r"^C\d+$", description="Идентификатор, напр. C1")
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    level: BloomLevel = Field(
        default=BloomLevel.APPLY, description="Целевой уровень по Блуму"
    )
    source_refs: list[str] = Field(default_factory=list)


class Outcome(BaseModel):
    """Измеримый результат обучения, привязанный к компетенции."""

    id: str = Field(..., pattern=r"^LO\d+$", description="Идентификатор, напр. LO3")
    competency_id: str = Field(..., pattern=r"^C\d+$")
    bloom: BloomLevel
    text: str = Field(..., min_length=1)
    source_refs: list[str] = Field(default_factory=list)