"""Тесты детерминированных проверок графа курса (Этап 2)."""

from core.models import BloomLevel, Brief, Competency, Hours, Module, Outcome
from validators.course import (
    check_hours_total,
    check_outcomes_referenced,
    check_prereq_cycles,
    validate_course,
)


def test_hours_ok() -> None:
    brief = Brief(topic="T", hours=Hours(lec=4, sem=2, self=1))
    modules = [Module(id="M1", title="M1", hours=Hours(lec=4, sem=2, self=1))]
    assert check_hours_total(brief, modules) == []


def test_hours_mismatch() -> None:
    brief = Brief(topic="T", hours=Hours(lec=10, sem=5, self=0))
    modules = [Module(id="M1", title="M1", hours=Hours(lec=8, sem=5, self=0))]
    problems = check_hours_total(brief, modules)
    assert any("Лекции" in p for p in problems)


def test_hours_zero_brief_skipped() -> None:
    brief = Brief(topic="T")
    modules = [Module(id="M1", title="M1", hours=Hours(lec=4, sem=2, self=1))]
    assert check_hours_total(brief, modules) == []


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
    brief = Brief(topic="T", hours=Hours(lec=4, sem=2, self=1))
    c = Competency(id="C1", name="C")
    lo = Outcome(id="LO1", competency_id="C1", bloom=BloomLevel.APPLY, text="X")
    m = Module(
        id="M1",
        title="M1",
        hours=Hours(lec=4, sem=2, self=1),
        outcomes=["LO1"],
    )
    assert validate_course(brief, [c], [lo], [m]) == []