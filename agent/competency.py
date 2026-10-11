from pydantic import BaseModel, Field
from core.models import Brief, Competency, Outcome
from llm.client import LLMClient
from agent.base import generate_structured
from agent.prompts.competency import (
    COMPETENCY_PROMPT_VERSION,
    COMPETENCY_SYSTEM_PROMPT,
)

__all__ = ["COMPETENCY_PROMPT_VERSION", "CompetencyPlan", "competency_agent"]


class CompetencyPlan(BaseModel):
    """Пакет компетенций и результатов обучения."""

    competencies: list[Competency] = Field(default_factory=list)
    outcomes: list[Outcome] = Field(default_factory=list)


async def competency_agent(llm: LLMClient, brief: Brief) -> CompetencyPlan:
    """Построить карту компетенций и результатов обучения по брифу."""
    return await generate_structured(
        llm,
        CompetencyPlan,
        COMPETENCY_SYSTEM_PROMPT,
        brief.model_dump_json(indent=2, ensure_ascii=False),
        temperature=0.3,
    )