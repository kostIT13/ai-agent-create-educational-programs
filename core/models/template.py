import enum
from pydantic import BaseModel, Field


class TemplateType(str, enum.Enum):
    """Два шаблона программ АЦР."""

    DPO = "dpo"  # ДПП ПК / стажировка (взрослые, профстандарты, удостоверение)
    GENERAL = "general"  # общеразвивающая (ЗУН, сертификат)


# Виды часов фиксированы кодом: у двух шаблонов АЦР разные виды работы,
# LLM не может придумать свой вид — только distribute часы по этим кодам.
TEMPLATE_HOURS_KINDS: dict[TemplateType, dict[str, str]] = {
    TemplateType.DPO: {
        "lk": "ЛК (лекции)",
        "pr": "ПР (практические)",
        "lb": "ЛБ (лабораторные)",
        "srs": "СРС (самостоятельная работа)",
        "ia": "ИА (итоговая аттестация)",
    },
    TemplateType.GENERAL: {
        "lec": "лекции (теория)",
        "sem": "практические занятия",
        "sr": "самостоятельная работа",
        "ia": "итоговая аттестация/контроль",
    },
}

# Реальные реквизиты нормативной базы (см. plan.md §0.3). Хранятся константами,
# чтобы агент не мог выдумать приказ или его номер.
TEMPLATE_LEGAL_BASE: dict[TemplateType, list[str]] = {
    TemplateType.DPO: [
        "ФЗ от 29.12.2012 № 273-ФЗ «Об образовании в Российской Федерации»",
        "Приказ Минобрнауки России № 499 "
        "(порядок организации образовательной деятельности по ДПО)",
    ],
    TemplateType.GENERAL: [
        "Приказ Минпросвещения России № 629 "
        "(порядок организации и осуществления образовательной деятельности "
        "по дополнительным общеобразовательным программам)",
    ],
}

TEMPLATE_DOC_ISSUED: dict[TemplateType, str] = {
    TemplateType.DPO: "Удостоверение о повышении квалификации установленного образца",
    TemplateType.GENERAL: "Сертификат об освоении программы",
}


class Template(BaseModel):
    """Выбранный шаблон АЦР: нормативка, выдаваемый документ, виды часов.

    Нормативная база и виды часов подставляются из констант кода
    (`build_template`), а не из ответа LLM — защита от выдуманных приказов.
    """

    template_type: TemplateType
    rationale: str = Field(default="", description="Обоснование выбора шаблона")
    legal_base: list[str] = Field(default_factory=list)
    doc_issued: str = Field(default="", description="Выдаваемый документ")
    hours_kinds: dict[str, str] = Field(
        default_factory=dict, description="Код вида часов -> название"
    )
    needs_clarification: bool = Field(
        default=False, description="Шаблон выбран недостаточно уверенно"
    )
    clarification: str = Field(default="", description="Вопрос методисту")


class TemplateChoice(BaseModel):
    """Structured output TemplateSelector'а: только выбор и обоснование.

    Реквизиты шаблона (нормативка, выдаваемый документ, виды часов)
    определяются кодом по template_type, а не моделью.
    """

    template_type: TemplateType
    rationale: str = Field(default="", min_length=1)
    needs_clarification: bool = False
    clarification: str = ""


def build_template(choice: TemplateChoice) -> Template:
    """Детерминированно собрать Template по выбору навыка (без LLM-деталей)."""
    return Template(
        template_type=choice.template_type,
        rationale=choice.rationale,
        legal_base=list(TEMPLATE_LEGAL_BASE[choice.template_type]),
        doc_issued=TEMPLATE_DOC_ISSUED[choice.template_type],
        hours_kinds=dict(TEMPLATE_HOURS_KINDS[choice.template_type]),
        needs_clarification=choice.needs_clarification,
        clarification=choice.clarification,
    )
