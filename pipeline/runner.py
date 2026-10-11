from loguru import logger
from core.models import CourseGraph
from llm.client import LLMClient, get_llm_client
from pipeline.workflow import build_workflow


class PipelineError(RuntimeError):
    """Пайплайн завершился, но валидация не пройдена."""


async def run_pipeline(
    raw_brief: str,
    llm: LLMClient | None = None,
) -> CourseGraph:
    """Прогнать бриф через пайплайн и вернуть граф курса (этап 2: без RAG)."""
    llm = llm or get_llm_client()
    graph = build_workflow(llm)
    state = await graph.ainvoke({"raw_brief": raw_brief})

    errors = state.get("errors") or []
    if errors:
        raise PipelineError("Валидация не пройдена:\n- " + "\n- ".join(errors))

    graph_result = CourseGraph(
        brief=state["brief"],
        competencies=state["competencies"],
        outcomes=state["outcomes"],
        modules=state["modules"],
    )
    logger.info(
        "Пайплайн завершён: компетенций={} результатов={} модулей={} часов={}",
        len(graph_result.competencies),
        len(graph_result.outcomes),
        len(graph_result.modules),
        graph_result.total_hours(),
    )
    return graph_result