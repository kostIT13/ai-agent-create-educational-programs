"""Планы лекций и структуры слайдов."""

from pydantic import BaseModel, Field


class SlideBlock(BaseModel):
    """Один слайд/блок лекции."""

    title: str = Field(..., min_length=1)
    bullets: list[str] = Field(default_factory=list, description="Тезисы")
    example: str = Field(default="", description="Пример")
    visual_type: str = Field(
        default="", description="Тип визуала: mermaid/table/code/image/..."
    )
    mermaid: str = Field(default="", description="Mermaid-код, если visual_type=mermaid")


class TimingStep(BaseModel):
    """Этап лекции и его длительность."""

    stage: str = Field(..., min_length=1)
    minutes: int = Field(..., ge=0)


class Lecture(BaseModel):
    """План лекции."""

    id: str = Field(..., pattern=r"^L\d+$", description="Идентификатор, напр. L2")
    module_id: str = Field(..., pattern=r"^M\d+$")
    title: str = Field(default="")
    outline: list[SlideBlock] = Field(default_factory=list)
    timing: list[TimingStep] = Field(default_factory=list)
    speaker_notes: str = Field(default="")
    source_refs: list[str] = Field(default_factory=list)