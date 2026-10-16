from core.models import Brief, Competency, Module, Outcome, Template


def check_hours_total(brief: Brief, modules: list[Module]) -> list[str]:
    """Сумма всех часов модулей должна совпадать с объёмом брифа (гейт перед контентом)."""
    problems: list[str] = []
    if brief.total_hours == 0:
        return problems  # объём не задан в брифе — не проверяем
    total = sum(m.total_hours for m in modules)
    if total != brief.total_hours:
        problems.append(
            f"Итог часов: у модулей {total} ч, в брифе {brief.total_hours} ч"
        )
    return problems


def check_hours_kinds(template: Template | None, modules: list[Module]) -> list[str]:
    """Часы ведутся только по видам работы шаблона (ЛК/ПР/ЛБ/СРС/ИА или
    лекции/практика/СР/ИА) — ловит аномалии вида «неизвестный вид часов»."""
    if template is None:
        return []
    problems: list[str] = []
    allowed = set(template.hours_kinds)
    for m in modules:
        unknown = sorted(set(m.hours) - allowed)
        if unknown:
            problems.append(
                f"Модуль {m.id}: неизвестные виды часов {', '.join(unknown)} "
                f"(шаблон допускает: {', '.join(sorted(allowed))})"
            )
        if m.total_hours == 0:
            problems.append(f"Модуль {m.id}: нулевая трудоёмкость")
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
    template: Template | None = None,
) -> list[str]:
    """Все проверки этапа Curriculum; возвращает список проблем (пустой = ок)."""
    problems: list[str] = []
    problems += check_hours_total(brief, modules)
    problems += check_hours_kinds(template, modules)
    problems += check_outcomes_referenced(modules, outcomes, competencies)
    problems += check_prereq_cycles(modules)
    # дедупликация с сохранением порядка
    return list(dict.fromkeys(problems))
