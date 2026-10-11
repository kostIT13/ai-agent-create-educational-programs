"""Детерминированные проверки графа курса (по §12.1 плана).

Используются на этапе Curriculum и позже — Critic'ом.
"""

from core.models import Brief, Competency, Module, Outcome


def check_hours_total(brief: Brief, modules: list[Module]) -> list[str]:
    """Сумма часов модулей должна совпадать с объёмом брифа (по каждому типу)."""
    problems: list[str] = []
    if brief.hours.total == 0:
        return problems  # объём не задан в брифе — не проверяем
    lec = sum(m.hours.lec for m in modules)
    sem = sum(m.hours.sem for m in modules)
    self_ = sum(m.hours.self for m in modules)
    if lec != brief.hours.lec:
        problems.append(f"Лекции: суммарно {lec} ч, в брифе {brief.hours.lec} ч")
    if sem != brief.hours.sem:
        problems.append(f"Семинары: суммарно {sem} ч, в брифе {brief.hours.sem} ч")
    if self_ != brief.hours.self:
        problems.append(f"Самост. работа: суммарно {self_} ч, в брифе {brief.hours.self} ч")
    return problems


def check_outcomes_referenced(
    modules: list[Module],
    outcomes: list[Outcome],
    competencies: list[Competency],
) -> list[str]:
    """Связность: outcomes существуют, привязаны к компетенциям и покрыты модулями."""
    problems: list[str] = []
    outcome_ids = {o.id for o in outcomes}
    competency_ids = {c.id for c in competencies}

    for m in modules:
        for oid in m.outcomes:
            if oid not in outcome_ids:
                problems.append(f"Модуль {m.id}: результат {oid} не существует")

    for o in outcomes:
        if o.competency_id not in competency_ids:
            problems.append(
                f"Результат {o.id}: компетенция {o.competency_id} не существует"
            )
        if not any(oid == o.id for m in modules for oid in m.outcomes):
            problems.append(f"Результат {o.id} не покрыт ни одним модулем")
    return problems


def check_prereq_cycles(modules: list[Module]) -> list[str]:
    """В графе пререквизитов не должно быть циклов и ссылок на несуществующие модули."""
    problems: list[str] = []
    module_ids = {m.id for m in modules}
    by_id = {m.id: m for m in modules}

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {m.id: WHITE for m in modules}

    def dfs(node: str, stack: list[str]) -> None:
        color[node] = GRAY
        stack.append(node)
        for nxt in by_id[node].prereq:
            if nxt not in module_ids:
                problems.append(f"Модуль {node}: пререквизит {nxt} не существует")
                continue
            if color[nxt] == GRAY:
                cycle = " -> ".join(stack[stack.index(nxt):] + [nxt])
                problems.append(f"Цикл в пререквизитах: {cycle}")
            elif color[nxt] == WHITE:
                dfs(nxt, stack)
        stack.pop()
        color[node] = BLACK

    for m in modules:
        if color[m.id] == WHITE:
            dfs(m.id, [])
    return problems


def validate_course(
    brief: Brief,
    competencies: list[Competency],
    outcomes: list[Outcome],
    modules: list[Module],
) -> list[str]:
    """Все проверки этапа Curriculum; возвращает список проблем (пустой = ок)."""
    problems: list[str] = []
    problems += check_hours_total(brief, modules)
    problems += check_outcomes_referenced(modules, outcomes, competencies)
    problems += check_prereq_cycles(modules)
    # дедупликация с сохранением порядка
    return list(dict.fromkeys(problems))