import pytest
from pydantic import ValidationError
from core.models import (
    BloomLevel,
    Brief,
    Competency,
    CourseGraph,
    Lecture,
    Module,
    Outcome,
    Question,
    QuestionType,
    Seminar,
    SlideBlock,
    Task,
    Template,
    TemplateChoice,
    TemplateType,
    TimingStep,
)
from core.models.template import build_template


def make_brief() -> Brief:
    return Brief(
        topic="Промпт-инжиниринг для продакт-менеджеров",
        goal="Научить PM проектировать и оценивать промпты",
        audience="Продакт-менеджеры",
        entry_level="Базовое понимание ИИ",
        total_hours=24,
        study_form="очно-заочная",
        final_assessment="защита проекта",
        language="ru",
        requirements=["Практика на реальных кейсах"],
        constraints=["Без математики"],
        references=["https://example.com/prompt-guide"],
    )


def make_template() -> Template:
    return build_template(
        TemplateChoice(template_type=TemplateType.GENERAL, rationale="интенсив")
    )


def make_graph() -> CourseGraph:
    brief = make_brief()
    c1 = Competency(
        id="C1", name="Проектирование промптов", level=BloomLevel.APPLY
    )
    lo1 = Outcome(
        id="LO1",
        competency_id="C1",
        bloom=BloomLevel.APPLY,
        text="Составляет промпт по шаблону",
    )
    m1 = Module(
        id="M1",
        title="Основы промптов",
        hours={"lec": 4, "sem": 2, "sr": 1},
        outcomes=["LO1"],
    )
    q1 = Question(
        id="Q1",
        module_id="M1",
        outcome_id="LO1",
        qtype=QuestionType.MCQ,
        prompt="Что такое temperature?",
        options=["0.2", "0.7", "1.0"],
        correct="0.7",
        difficulty=0.4,
        explanation="Temperature управляет случайностью вывода.",
    )
    s1 = Seminar(
        id="S1",
        module_id="M1",
        tasks=[Task(id="T1", title="Задача", description="Условие задачи")],
        rubric={"Корректность": 5},
    )
    l1 = Lecture(
        id="L1",
        module_id="M1",
        outline=[SlideBlock(title="Введение", bullets=["a", "b"])],
        timing=[TimingStep(stage="Введение", minutes=5)],
    )
    return CourseGraph(
        brief=brief,
        template=make_template(),
        competencies=[c1],
        outcomes=[lo1],
        modules=[m1],
        questions=[q1],
        seminars=[s1],
        lectures=[l1],
    )


def test_brief_defaults() -> None:
    brief = Brief(topic="T")
    assert brief.total_hours == 0
    assert brief.template_hint == "auto"
    assert brief.missing == []
    assert brief.language == "ru"
    assert brief.requirements == []
    assert brief.constraints == []


def test_module_total_hours_by_kinds() -> None:
    m = Module(id="M1", title="M", hours={"lk": 6, "pr": 4, "lb": 0, "srs": 8, "ia": 2})
    assert m.total_hours == 20


def test_graph_roundtrip_json() -> None:
    graph = make_graph()
    data = graph.model_dump_json()
    restored = CourseGraph.model_validate_json(data)
    assert restored == graph


def test_graph_helpers() -> None:
    graph = make_graph()
    assert graph.total_hours() == 7
    assert graph.template is not None
    assert graph.template.template_type is TemplateType.GENERAL
    assert graph.module_by_id("M1") is not None
    assert graph.module_by_id("M9") is None
    assert graph.outcome_by_id("LO1") is not None
    assert graph.competency_by_id("C1") is not None


def test_invalid_ids() -> None:
    with pytest.raises(ValidationError):
        Competency(id="bad", name="X")
    with pytest.raises(ValidationError):
        Module(id="X1", title="M")


def test_difficulty_range() -> None:
    with pytest.raises(ValidationError):
        Question(
            id="Q1",
            module_id="M1",
            outcome_id="LO1",
            qtype=QuestionType.MCQ,
            prompt="p",
            difficulty=1.5,
        )


def test_negative_hours_rejected() -> None:
    with pytest.raises(ValidationError):
        Module(id="M1", title="M", hours={"lec": -1})
