from pydantic import BaseModel, Field, NonNegativeInt


class Module(BaseModel):
    id: str = Field(..., pattern=r"^M\d+$", description="Идентификатор, напр. M2")
    title: str = Field(..., min_length=1)
    summary: str = Field(default="")
    hours: dict[str, NonNegativeInt] = Field(
        default_factory=dict,
        description="Часы по видам работы шаблона (коды из Template.hours_kinds)",
    )
    outcomes: list[str] = Field(
        default_factory=list, description="id результатов обучения"
    )
    prereq: list[str] = Field(
        default_factory=list, description="id модулей-пререквизитов"
    )
    source_refs: list[str] = Field(default_factory=list)

    @property
    def total_hours(self) -> int:
        return sum(self.hours.values())
