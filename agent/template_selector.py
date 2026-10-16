from core.models import Brief, Template, TemplateChoice, TemplateType
from core.models.template import build_template
from llm.client import LLMClient
from agent.base import generate_structured
from agent.prompts.template_selector import (
    TEMPLATE_SELECTOR_PROMPT_VERSION,
    TEMPLATE_SELECTOR_SYSTEM_PROMPT,
)

__all__ = ["TEMPLATE_SELECTOR_PROMPT_VERSION", "template_selector_agent"]


async def template_selector_agent(
    llm: LLMClient, brief: Brief, *, context: str = ""
) -> Template:
    """Выбрать шаблон АЦР по брифу.

    Нормативная база, выдаваемый документ и виды часов закреплены кодом
    (`build_template`) — LLM не может выдумать приказ или вид часов.
    Явный `template_hint` из брифа коротко замыкает выбор без LLM-вызова.
    """
    if brief.template_hint != "auto":
        return build_template(
            TemplateChoice(
                template_type=TemplateType(brief.template_hint),
                rationale="Шаблон явно указан в брифе",
            )
        )
    choice = await generate_structured(
        llm,
        TemplateChoice,
        TEMPLATE_SELECTOR_SYSTEM_PROMPT,
        brief.model_dump_json(indent=2, ensure_ascii=False),
        context=context,
        temperature=0.1,
    )
    return build_template(choice)
