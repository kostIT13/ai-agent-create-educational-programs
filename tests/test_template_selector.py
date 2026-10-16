"""Тесты TemplateSelector: реквизиты шаблонов закреплены кодом, LLM только выбирает."""

from typing import Any

import pytest

from agent.template_selector import template_selector_agent
from core.models import Brief, TemplateChoice, TemplateType
from core.models.template import build_template


def test_build_template_dpo_constants() -> None:
    t = build_template(
        TemplateChoice(template_type=TemplateType.DPO, rationale="ПК для банка")
    )
    assert list(t.hours_kinds) == ["lk", "pr", "lb", "srs", "ia"]
    assert any("499" in lb for lb in t.legal_base)
    assert any("273-ФЗ" in lb for lb in t.legal_base)
    assert "Удостоверение" in t.doc_issued
    assert not t.needs_clarification


def test_build_template_general_constants() -> None:
    t = build_template(
        TemplateChoice(
            template_type=TemplateType.GENERAL,
            rationale="интенсив для школьников",
            needs_clarification=True,
            clarification="Программа детская или для взрослых?",
        )
    )
    assert list(t.hours_kinds) == ["lec", "sem", "sr", "ia"]
    assert any("629" in lb for lb in t.legal_base)
    assert "Сертификат" in t.doc_issued
    assert t.needs_clarification
    assert t.clarification


class ExplodingLLM:
    """LLM не должен вызываться при явном template_hint."""

    def structured(self, schema: type, **kwargs: Any) -> Any:
        raise AssertionError("LLM вызван, хотя шаблон задан явно")


@pytest.mark.asyncio
async def test_explicit_hint_short_circuits_llm() -> None:
    brief = Brief(topic="ПК по анализу данных", template_hint="dpo")
    t = await template_selector_agent(ExplodingLLM(), brief)
    assert t.template_type is TemplateType.DPO
    assert t.rationale == "Шаблон явно указан в брифе"


class FakeStructured:
    def __init__(self, result: Any) -> None:
        self.result = result

    async def ainvoke(self, messages: Any) -> Any:
        return self.result


class FakeLLM:
    def __init__(self, choice: TemplateChoice) -> None:
        self._choice = choice

    def structured(self, schema: type, **kwargs: Any) -> FakeStructured:
        assert schema is TemplateChoice
        return FakeStructured(self._choice)


@pytest.mark.asyncio
async def test_llm_choice_gets_code_fixed_details() -> None:
    """Ответ LLM влияет только на template_type/rationale — реквизиты из кода."""
    brief = Brief(topic="Интенсив по ИИ", template_hint="auto")
    llm = FakeLLM(
        TemplateChoice(
            template_type=TemplateType.GENERAL, rationale="24 часа, школьники"
        )
    )
    t = await template_selector_agent(llm, brief)
    assert t.template_type is TemplateType.GENERAL
    assert t.rationale == "24 часа, школьники"
    assert list(t.hours_kinds) == ["lec", "sem", "sr", "ia"]
    assert any("629" in lb for lb in t.legal_base)
