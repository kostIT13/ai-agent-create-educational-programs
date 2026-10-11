"""Семинары и практические задания."""

from pydantic import BaseModel, Field


class Task(BaseModel):
    """Практическое задание семинара."""

    id: str = Field(..., pattern=r"^T\d+$", description="Идентификатор, напр. T1")
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1, description="Условие задачи")
    data: str = Field(default="", description="Данные/материалы")
    success_criteria: list[str] = Field(default_factory=list)
    reference_solution: str = Field(default="", description="Эталонное решение")
    source_refs: list[str] = Field(default_factory=list)


class Seminar(BaseModel):
    """Семинар модуля."""

    id: str = Field(..., pattern=r"^S\d+$", description="Идентификатор, напр. S2")
    module_id: str = Field(..., pattern=r"^M\d+$")
    title: str = Field(default="")
    tasks: list[Task] = Field(default_factory=list)
    rubric: dict[str, int] = Field(
        default_factory=dict, description="Критерий → баллы"
    )
    source_refs: list[str] = Field(default_factory=list)