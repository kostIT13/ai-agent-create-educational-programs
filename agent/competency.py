import json
from pydantic import BaseModel, Field
from core.models import Brief, Competency, Outcome, Template
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


async def competency_agent(
    llm: LLMClient,
    brief: Brief,
    template: Template,
    *,
    context: str = "",
) -> CompetencyPlan:
    """Построить карту компетенций и результатов обучения по брифу и шаблону АЦР.

    `context` — чанки референсов в `<source>`-обёртке (опционально).
    """
    payload = {
        "brief": brief.model_dump(),
        "template": {
            "template_type": template.template_type.value,
            "doc_issued": template.doc_issued,
            "legal_base": template.legal_base,
        },
    }
    return await generate_structured(
        llm,
        CompetencyPlan,
        COMPETENCY_SYSTEM_PROMPT,
        json.dumps(payload, ensure_ascii=False, indent=2),
        context=context,
        temperature=0.3,
    )
