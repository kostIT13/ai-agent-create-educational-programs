import enum
from pydantic import BaseModel, Field


class QuestionType(str, enum.Enum):
    """Типы тестовых вопросов."""

    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    MATCHING = "matching"
    OPEN = "open"


class Question(BaseModel):
    """Тестовый вопрос, привязанный к модулю и результату обучения."""

    id: str = Field(..., pattern=r"^Q\d+$", description="Идентификатор, напр. Q41")
    module_id: str = Field(..., pattern=r"^M\d+$")
    outcome_id: str = Field(..., pattern=r"^LO\d+$")
    qtype: QuestionType
    prompt: str = Field(..., min_length=1)
    options: list[str] | None = Field(
        default=None, description="Варианты для mcq/matching"
    )
    correct: str | None = Field(default=None, description="Правильный ответ")
    distractors_note: str | None = Field(
        default=None, description="Пояснение к дистракторам"
    )
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0, description="0..1")
    explanation: str = Field(default="")
    source_refs: list[str] = Field(default_factory=list)