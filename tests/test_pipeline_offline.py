from typing import Any
import pytest
from agent.competency import CompetencyPlan
from agent.curriculum import ModulePlan
from core.models import (
    BloomLevel,
    Brief,
    Competency,
    Module,
    Outcome,
    TemplateChoice,
    TemplateType,
)
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

    def __init__(
        self,
        brief: Brief,
        choice: TemplateChoice,
        plan: CompetencyPlan,
        modules: ModulePlan,
    ) -> None:
        self._brief = brief
        self._choice = choice
        self._plan = plan
        self._modules = modules
        self.choice_calls = 0

    def structured(self, schema: type, **kwargs: Any) -> FakeStructured:
        if schema is Brief:
            return FakeStructured(self._brief)
        if schema is TemplateChoice:
            self.choice_calls += 1
            return FakeStructured(self._choice)
        if schema is CompetencyPlan:
            return FakeStructured(self._plan)
        if schema is ModulePlan:
            return FakeStructured(self._modules)
        raise AssertionError(f"Неожиданная схема: {schema}")


def make_brief(total_hours: int = 7) -> Brief:
    return Brief(
        topic="Курс по X",
        audience="взрослые",
        entry_level="базовый",
        total_hours=total_hours,
        study_form="очно-заочная",
        final_assessment="зачёт",
    )


def make_fake_llm(brief: Brief | None = None) -> FakeLLM:
    brief = brief or make_brief()
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
                hours={"lec": 4, "sem": 2, "sr": 1},
                outcomes=["LO1"],
            )
        ]
    )
    choice = TemplateChoice(
        template_type=TemplateType.GENERAL, rationale="интенсив для общей аудитории"
    )
    return FakeLLM(brief, choice, plan, modules)


@pytest.mark.asyncio
async def test_pipeline_full_run() -> None:
    graph = build_workflow(make_fake_llm())
    state = await graph.ainvoke({"raw_brief": "Курс по X на 7 часов"})

    assert state["errors"] == []
    assert state["brief"].topic == "Курс по X"
    assert state["template"].template_type is TemplateType.GENERAL
    assert state["template"].hours_kinds.keys() == {"lec", "sem", "sr", "ia"}
    assert any("629" in lb for lb in state["template"].legal_base)
    assert len(state["competencies"]) == 1
    assert len(state["outcomes"]) == 1
    assert len(state["modules"]) == 1
    assert state["modules"][0].outcomes == ["LO1"]


@pytest.mark.asyncio
async def test_explicit_template_hint_skips_llm() -> None:
    """Явный hint из брифа коротко замыкает выбор — LLM не дёргается."""
    brief = make_brief()
    brief.template_hint = "dpo"
    llm = make_fake_llm(brief)
    graph = build_workflow(llm)
    state = await graph.ainvoke({"raw_brief": "ПК по X на 7 часов"})

    assert llm.choice_calls == 0
    assert state["template"].template_type is TemplateType.DPO
    assert state["template"].hours_kinds.keys() == {"lk", "pr", "lb", "srs", "ia"}


@pytest.mark.asyncio
async def test_pipeline_validation_errors_collected() -> None:
    """Часы модулей не сходятся с брифом -> errors в финальном состоянии."""
    brief = make_brief(total_hours=10)
    llm = make_fake_llm(brief)
    graph = build_workflow(llm)
    state = await graph.ainvoke({"raw_brief": "T"})

    assert state["errors"], "Ожидались ошибки валидации"
    assert any("Итог часов" in p for p in state["errors"])
