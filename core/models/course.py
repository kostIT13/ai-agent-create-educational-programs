"""Граф курса — единый источник правды (по §7.1 плана)."""

from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from core.models.assessment import Question
from core.models.brief import Brief
from core.models.competency import Competency, Outcome
from core.models.lecture import Lecture
from core.models.module import Module
from core.models.seminar import Seminar


class CriticIssue(BaseModel):
    """Замечание Critic'а."""

    severity: Literal["error", "warning", "info"] = "warning"
    entity_type: str = Field(..., description="Тип сущности: module/question/seminar/...")
    entity_id: str = Field(default="", description="id сущности")
    message: str = Field(..., min_length=1)


class CriticReport(BaseModel):
    """Отчёт Critic'а по всему графу."""

    issues: list[CriticIssue] = Field(default_factory=list)
    passed: bool = False
    iterations: int = Field(default=0, ge=0)


class CourseGraph(BaseModel):
    """Полный граф курса: компетенции → результаты → модули → артефакты."""

    brief: Brief
    competencies: list[Competency] = Field(default_factory=list)
    outcomes: list[Outcome] = Field(default_factory=list)
    modules: list[Module] = Field(default_factory=list)
    questions: list[Question] = Field(default_factory=list)
    seminars: list[Seminar] = Field(default_factory=list)
    lectures: list[Lecture] = Field(default_factory=list)
    critic_report: CriticReport | None = Field(default=None)

    def total_hours(self) -> int:
        """Суммарный объём всех модулей в часах."""
        return sum(m.hours.total for m in self.modules)

    def module_by_id(self, module_id: str) -> Module | None:
        return next((m for m in self.modules if m.id == module_id), None)

    def outcome_by_id(self, outcome_id: str) -> Outcome | None:
        return next((o for o in self.outcomes if o.id == outcome_id), None)

    def competency_by_id(self, competency_id: str) -> Competency | None:
        return next((c for c in self.competencies if c.id == competency_id), None)


class CourseState(TypedDict, total=False):
    """Состояние LangGraph-пайплайна.

    Чанки референсов в state не кладём — только id; контент достаём из векторной БД по месту.
    """

    brief: Brief
    competencies: list[Competency]
    outcomes: list[Outcome]
    modules: list[Module]
    questions: list[Question]
    seminars: list[Seminar]
    lectures: list[Lecture]
    critic_report: CriticReport | None
    errors: list[str]