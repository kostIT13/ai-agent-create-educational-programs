import pytest

from core.models import (
    BloomLevel,
    Brief,
    Competency,
    Module,
    Outcome,
    TemplateChoice,
    TemplateType,
)
from core.models.template import build_template
from validators.course import (
    check_hours_kinds,
    check_hours_total,
    check_outcomes_referenced,
    check_prereq_cycles,
    validate_course,
)


def dpo_template() -> TemplateChoice:
    return build_template(
        TemplateChoice(template_type=TemplateType.DPO, rationale="ПК")
    )


def general_template() -> TemplateChoice:
    return build_template(
        TemplateChoice(template_type=TemplateType.GENERAL, rationale="интенсив")
    )


def test_hours_total_ok() -> None:
    brief = Brief(topic="T", total_hours=20)
    modules = [Module(id="M1", title="M1", hours={"lk": 6, "pr": 4, "srs": 10})]
    assert check_hours_total(brief, modules) == []


def test_hours_total_mismatch() -> None:
    """Кейс из данных АЦР: заявленный объём не сходится с итогом таблиц."""
    brief = Brief(topic="T", total_hours=246)
    modules = [
        Module(id="M1", title="M1", hours={"srs": 246}),
        Module(id="M2", title="M2", hours={"pr": 66, "lb": 6}),
    ]
    problems = check_hours_total(brief, modules)
    assert any("Итог часов" in p for p in problems)


def test_hours_zero_brief_skipped() -> None:
    brief = Brief(topic="T")
    modules = [Module(id="M1", title="M1", hours={"lk": 4})]
    assert check_hours_total(brief, modules) == []


def test_hours_kinds_ok_for_template() -> None:
    modules = [Module(id="M1", title="M1", hours={"lk": 4, "pr": 2, "srs": 4})]
    assert check_hours_kinds(dpo_template(), modules) == []


def test_hours_kinds_foreign_kind_detected() -> None:
    """В dpo-шаблоне нет вида 'sr' (это из general) — валидатор должен ругнуться."""
    modules = [Module(id="M1", title="M1", hours={"lk": 4, "sr": 2})]
    problems = check_hours_kinds(dpo_template(), modules)
    assert any("sr" in p for p in problems)


def test_hours_kinds_zero_module_detected() -> None:
    modules = [Module(id="M1", title="M1", hours={"lk": 0})]
    problems = check_hours_kinds(general_template(), modules)
    assert any("нулевая" in p for p in problems)


def test_hours_kinds_skipped_without_template() -> None:
    modules = [Module(id="M1", title="M1", hours={"anything": 1})]
    assert check_hours_kinds(None, modules) == []


def test_outcomes_referenced_ok() -> None:
    c = Competency(id="C1", name="C")
    lo = Outcome(id="LO1", competency_id="C1", bloom=BloomLevel.APPLY, text="X")
    m = Module(id="M1", title="M1", outcomes=["LO1"])
    assert check_outcomes_referenced([m], [lo], [c]) == []


def test_missing_outcome_detected() -> None:
    c = Competency(id="C1", name="C")
    lo = Outcome(id="LO1", competency_id="C1", bloom=BloomLevel.APPLY, text="X")
    m = Module(id="M1", title="M1", outcomes=["LO99"])
    problems = check_outcomes_referenced([m], [lo], [c])
    assert any("LO99" in p for p in problems)


def test_outcome_not_covered_detected() -> None:
    c = Competency(id="C1", name="C")
    lo = Outcome(id="LO1", competency_id="C1", bloom=BloomLevel.APPLY, text="X")
    m = Module(id="M1", title="M1", outcomes=[])
    problems = check_outcomes_referenced([m], [lo], [c])
    assert any("не покрыт" in p for p in problems)


def test_dangling_competency_detected() -> None:
    c = Competency(id="C1", name="C")
    lo = Outcome(id="LO1", competency_id="C9", bloom=BloomLevel.APPLY, text="X")
    m = Module(id="M1", title="M1", outcomes=["LO1"])
    problems = check_outcomes_referenced([m], [lo], [c])
    assert any("C9" in p for p in problems)


def test_prereq_cycle_detected() -> None:
    m1 = Module(id="M1", title="M1", prereq=["M2"])
    m2 = Module(id="M2", title="M2", prereq=["M1"])
    problems = check_prereq_cycles([m1, m2])
    assert any("Цикл" in p for p in problems)


def test_prereq_missing_module_detected() -> None:
    m1 = Module(id="M1", title="M1", prereq=["M9"])
    problems = check_prereq_cycles([m1])
    assert any("не существует" in p for p in problems)


def test_valid_course_passes_all_checks() -> None:
    brief = Brief(topic="T", total_hours=10)
    c = Competency(id="C1", name="C")
    lo = Outcome(id="LO1", competency_id="C1", bloom=BloomLevel.APPLY, text="X")
    m = Module(
        id="M1",
        title="M1",
        hours={"lk": 4, "pr": 2, "srs": 4},
        outcomes=["LO1"],
    )
    assert validate_course(brief, [c], [lo], [m], dpo_template()) == []


def test_validate_course_blocks_on_hours_gate() -> None:
    """Часы не сходятся — курс не проходит гейт перед генерацией контента."""
    brief = Brief(topic="T", total_hours=72)
    c = Competency(id="C1", name="C")
    lo = Outcome(id="LO1", competency_id="C1", bloom=BloomLevel.APPLY, text="X")
    m = Module(id="M1", title="M1", hours={"lk": 4, "pr": 2, "srs": 4}, outcomes=["LO1"])
    problems = validate_course(brief, [c], [lo], [m], dpo_template())
    assert any("Итог часов" in p for p in problems)
