from pydantic import BaseModel, Field
from core.models.brief import Hours


class Module(BaseModel):
    id: str = Field(..., pattern=r"^M\d+$", description="Идентификатор, напр. M2")
    title: str = Field(..., min_length=1)
    summary: str = Field(default="")
    hours: Hours = Field(default_factory=Hours)
    outcomes: list[str] = Field(
        default_factory=list, description="id результатов обучения"
    )
    prereq: list[str] = Field(
        default_factory=list, description="id модулей-пререквизитов"
    )
    source_refs: list[str] = Field(default_factory=list)