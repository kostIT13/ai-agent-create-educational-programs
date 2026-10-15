from typing import Any

from loguru import logger

from agent.competency import competency_agent
from agent.curriculum import curriculum_agent
from agent.intake import intake_agent
from core.models import CourseState
from llm.client import LLMClient
from rag.retriever import Retriever
from validators.course import validate_course


def make_nodes(
    llm: LLMClient,
    retriever: Retriever | None = None,
) -> dict[str, Any]:
    """Собрать узлы графа, замыкая их на конкретный LLM-клиент и ретривер.

    Если `retriever` не передан (или референсов нет) — агенты работают без
    контекста: `Retriever.search` вернёт пустой список, `source_refs` останутся
    пустыми (режим «без референсов»).
    """

    async def _context(query: str) -> str:
        if retriever is None:
            return ""
        chunks = await retriever.search(query)
        return retriever.to_source_block(chunks)

    async def intake_node(state: CourseState) -> dict[str, Any]:
        raw = state.get("raw_brief") or ""
        brief = await intake_agent(llm, raw)
        return {"brief": brief}

    async def competency_node(state: CourseState) -> dict[str, Any]:
        brief = state["brief"]
        context = await _context(
            f"Требования к выпускнику и компетенции по теме: {brief.topic}"
        )
        plan = await competency_agent(llm, brief, context=context)
        logger.debug(
            "Competency: competencies={} outcomes={} refs={}",
            len(plan.competencies),
            len(plan.outcomes),
            sum(len(c.source_refs) for c in plan.competencies),
        )
        return {"competencies": plan.competencies, "outcomes": plan.outcomes}

    async def curriculum_node(state: CourseState) -> dict[str, Any]:
        brief = state["brief"]
        context = await _context(
            f"Структура и часы учебной программы по теме: {brief.topic}"
        )
        modules = await curriculum_agent(
            llm, brief, state["outcomes"], context=context
        )
        logger.debug(
            "Curriculum: modules={} refs={}",
            len(modules),
            sum(len(m.source_refs) for m in modules),
        )
        return {"modules": modules}

    async def validate_node(state: CourseState) -> dict[str, Any]:
        problems = validate_course(
            state["brief"],
            state["competencies"],
            state["outcomes"],
            state["modules"],
        )
        return {"errors": problems}

    return {
        "intake": intake_node,
        "competency": competency_node,
        "curriculum": curriculum_node,
        "validate": validate_node,
    }