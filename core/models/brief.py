"""Входные данные: бриф пользователя (по §3.1 плана)."""

from pydantic import BaseModel, Field


class Hours(BaseModel):
    """Объём курса в часах по форматам занятий."""

    lec: int = Field(default=0, ge=0, description="Лекции")
    sem: int = Field(default=0, ge=0, description="Семинары/лабы")
    self: int = Field(default=0, ge=0, description="Самостоятельная работа")

    @property
    def total(self) -> int:
        return self.lec + self.sem + self.self


class Brief(BaseModel):
    """Структурированный бриф курса — результат работы Intake-агента."""

    topic: str = Field(..., min_length=1, description="Тема курса")
    goal: str = Field(default="", description="Цель курса")
    audience: str = Field(default="", description="Целевая аудитория")
    entry_level: str = Field(default="", description="Входной уровень слушателей")
    hours: Hours = Field(default_factory=Hours, description="Объём в часах")
    language: str = Field(default="ru", description="Язык курса")
    requirements: list[str] = Field(
        default_factory=list, description="Обязательные темы/требования"
    )
    constraints: list[str] = Field(default_factory=list, description="Ограничения")
    references: list[str] = Field(
        default_factory=list, description="Референсы (URL/названия)"
    )