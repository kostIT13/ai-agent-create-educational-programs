"""Сборка LangGraph-графа: intake -> competency -> curriculum -> validate."""

from langgraph.graph import END, START, StateGraph

from core.models import CourseState
from llm.client import LLMClient
from pipeline.nodes import make_nodes


def build_workflow(llm: LLMClient):
    """Скомпилированный граф пайплайна (линейный на этом этапе)."""
    nodes = make_nodes(llm)
    builder = StateGraph(CourseState)

    builder.add_node("intake", nodes["intake"])
    builder.add_node("competency", nodes["competency"])
    builder.add_node("curriculum", nodes["curriculum"])
    builder.add_node("validate", nodes["validate"])

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "competency")
    builder.add_edge("competency", "curriculum")
    builder.add_edge("curriculum", "validate")
    builder.add_edge("validate", END)

    return builder.compile()