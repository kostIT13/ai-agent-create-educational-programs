from typing import Any
from llm.client import LLMClient
from agent.competency import competency_agent
from agent.curriculum import curriculum_agent
from agent.intake import intake_agent
from core.models import CourseState
from validators.course import validate_course


def make_nodes(llm: LLMClient) -> dict[str, Any]:
    """Собрать узлы графа, замыкая их на конкретный LLM-клиент."""

    async def intake_node(state: CourseState) -> dict[str, Any]:
        raw = state.get("raw_brief") or ""
        brief = await intake_agent(llm, raw)
        return {"brief": brief}

    async def competency_node(state: CourseState) -> dict[str, Any]:
        plan = await competency_agent(llm, state["brief"])
        return {"competencies": plan.competencies, "outcomes": plan.outcomes}

    async def curriculum_node(state: CourseState) -> dict[str, Any]:
        modules = await curriculum_agent(llm, state["brief"], state["outcomes"])
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