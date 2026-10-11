"""Offline-тесты LangGraph-пайплайна с фейковым LLM (без реальных вызовов)."""

from typing import Any

import pytest

from agent.competency import CompetencyPlan
from agent.curriculum import ModulePlan
from core.models import BloomLevel, Brief, Competency, Hours, Module, Outcome
from pipeline.workflow import build_workflow


class FakeStructured:
    """Имитация runnable со structured output."""

    def __init__(self, result: Any) -> None:
        self.result = result

    async def ainvoke(self, messages: Any) -> Any:
        return self.result

    def with_fallbacks(self, *args: Any, **kwargs: Any) -> "FakeStructured":
        return self


class FakeLLM:
    """Имитация LLMClient: возвращает предзаданные ответы по схеме."""

    def __init__(self, brief: Brief, plan: CompetencyPlan, modules: ModulePlan) -> None:
        self._brief = brief
        self._plan = plan
        self._modules = modules

    def structured(self, schema: type, **kwargs: Any) -> FakeStructured:
        if schema is Brief:
            return FakeStructured(self._brief)
        if schema is CompetencyPlan:
            return FakeStructured(self._plan)
        if schema is ModulePlan:
            return FakeStructured(self._modules)
        raise AssertionError(f"Неожиданная схема: {schema}")


def make_fake_llm(brief: Brief | None = None) -> FakeLLM:
    brief = brief or Brief(topic="Курс по X", hours=Hours(lec=4, sem=2, self=1))
    c1 = Competency(id="C1", name="Компетенция 1", level=BloomLevel.APPLY)
    lo1 = Outcome(
        id="LO1",
        competency_id="C1",
        bloom=BloomLevel.APPLY,
        text="Применяет метод X",
    )
    plan = CompetencyPlan(competencies=[c1], outcomes=[lo1])
    modules = ModulePlan(
        modules=[
            Module(
                id="M1",
                title="Модуль 1",
                hours=Hours(lec=4, sem=2, self=1),
                outcomes=["LO1"],
            )
        ]
    )
    return FakeLLM(brief, plan, modules)


@pytest.mark.asyncio
async def test_pipeline_full_run() -> None:
    graph = build_workflow(make_fake_llm())
    state = await graph.ainvoke({"raw_brief": "Курс по X на 7 часов"})

    assert state["errors"] == []
    assert state["brief"].topic == "Курс по X"
    assert len(state["competencies"]) == 1
    assert len(state["outcomes"]) == 1
    assert len(state["modules"]) == 1
    assert state["modules"][0].outcomes == ["LO1"]


@pytest.mark.asyncio
async def test_pipeline_validation_errors_collected() -> None:
    """Модули с неверными часами -> errors в финальном состоянии."""
    brief = Brief(topic="T", hours=Hours(lec=10, sem=0, self=0))
    llm = make_fake_llm(brief)
    graph = build_workflow(llm)
    state = await graph.ainvoke({"raw_brief": "T"})

    assert state["errors"], "Ожидались ошибки валидации"
    assert any("Лекции" in p for p in state["errors"])