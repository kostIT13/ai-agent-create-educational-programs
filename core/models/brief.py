from typing import Literal
from pydantic import BaseModel, Field

# Только эти поля Intake имеет право требовать уточнением у методиста (plan.md §3.1).
CLARIFIABLE_FIELDS = (
    "audience",
    "entry_level",
    "total_hours",
    "study_form",
    "final_assessment",
)


class Brief(BaseModel):
    """Структурированный бриф курса — результат работы Intake-агента."""

    topic: str = Field(..., min_length=1, description="Тема курса")
    goal: str = Field(default="", description="Цель курса")
    audience: str = Field(default="", description="Целевая аудитория")
    entry_level: str = Field(default="", description="Входной уровень слушателей")
    total_hours: int = Field(
        default=0, ge=0, description="Общий объём программы в часах (по ТЗ 16..500)"
    )
    study_form: str = Field(
        default="", description="Форма обучения (очная/очно-заочная/с ЭО и ДОТ)"
    )
    final_assessment: str = Field(
        default="", description="Форма итоговой аттестации (защита проекта/зачёт/тест)"
    )
    template_hint: Literal["auto", "dpo", "general"] = Field(
        default="auto",
        description="Явный сигнал шаблона из запроса: dpo (ПК/стажировка), "
        "general (общеразвивающая) или auto (определяет TemplateSelector)",
    )
    missing: list[str] = Field(
        default_factory=list,
        description="Названия полей брифа без которых каркас не построить — "
        "кандидаты на уточняющие вопросы методисту",
    )
    language: str = Field(default="ru", description="Язык курса")
    requirements: list[str] = Field(
        default_factory=list, description="Обязательные темы/требования"
    )
    constraints: list[str] = Field(default_factory=list, description="Ограничения")
    references: list[str] = Field(
        default_factory=list, description="Референсы (URL/названия)"
    )
