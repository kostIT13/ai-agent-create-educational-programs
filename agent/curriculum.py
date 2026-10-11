import json
from pydantic import BaseModel, Field
from core.models import Brief, Module, Outcome
from llm.client import LLMClient
from agent.base import generate_structured
from agent.prompts.curriculum import (
    CURRICULUM_PROMPT_VERSION,
    CURRICULUM_SYSTEM_PROMPT,
)

__all__ = ["CURRICULUM_PROMPT_VERSION", "ModulePlan", "curriculum_agent"]


class ModulePlan(BaseModel):
    """Пакет модулей курса."""

    modules: list[Module] = Field(default_factory=list)


async def curriculum_agent(
    llm: LLMClient,
    brief: Brief,
    outcomes: list[Outcome],
) -> list[Module]:
    """Построить модули курса по брифу и результатам обучения."""
    payload = {
        "brief": brief.model_dump(),
        "outcomes": [o.model_dump() for o in outcomes],
    }
    user_content = json.dumps(payload, ensure_ascii=False, indent=2)
    plan = await generate_structured(
        llm,
        ModulePlan,
        CURRICULUM_SYSTEM_PROMPT,
        user_content,
        temperature=0.2,
    )
    return plan.modules