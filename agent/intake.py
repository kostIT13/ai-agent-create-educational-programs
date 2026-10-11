from core.models import Brief
from llm.client import LLMClient
from agent.base import generate_structured
from agent.prompts.intake import INTAKE_PROMPT_VERSION, INTAKE_SYSTEM_PROMPT

__all__ = ["INTAKE_PROMPT_VERSION", "intake_agent"]


async def intake_agent(llm: LLMClient, raw_brief: str) -> Brief:
    return await generate_structured(
        llm,
        Brief,
        INTAKE_SYSTEM_PROMPT,
        raw_brief,
        temperature=0.2,
    )