"""Тесты чанкинга по структуре документа (rag/chunking.py)."""

from rag.chunking import chunk_markdown


def test_chunks_by_headings() -> None:
    md = """# Введение

Общий вводный текст о курсе, который описывает цели и задачи обучения.

## 1. Цели

Цель курса — научить студентов проектировать и применять методы машинного обучения.

## 2. Результаты

Студент умеет применять изученные методы на практике и анализировать результаты.
"""
    chunks = chunk_markdown(md, file="program.md")
    assert len(chunks) == 3
    assert chunks[0].section == "Введение"
    assert chunks[1].section == "1. Цели"
    assert chunks[2].section == "2. Результаты"
    assert all(c.file == "program.md" for c in chunks)


def test_chunk_metadata() -> None:
    md = "# Раздел\n\nТекст раздела достаточно длинный, чтобы не быть отброшенным фильтром."
    chunks = chunk_markdown(
        md, file="fgos.pdf", source_type="standard", date="2024-01-01"
    )
    assert len(chunks) == 1
    assert chunks[0].source_type == "standard"
    assert chunks[0].date == "2024-01-01"
    assert chunks[0].section == "Раздел"


def test_empty_and_short_blocks_skipped() -> None:
    md = (
        "# Пустой раздел\n\n"
        "# Короткий\n\nx\n\n"
        "# Нормальный\n\nДостаточно длинный текст раздела, который проходит фильтр."
    )
    chunks = chunk_markdown(md, file="a.md")
    # "x" короче MIN_CHUNK_CHARS — пропускается
    assert len(chunks) == 1
    assert chunks[0].section == "Нормальный"


def test_text_before_first_heading() -> None:
    md = "Вводный абзац без заголовка, достаточно длинный для фильтра.\n\n# Раздел\n\nТекст раздела."
    chunks = chunk_markdown(md, file="a.md")
    assert chunks[0].section == ""
    assert "Вводный абзац" in chunks[0].text


def test_long_block_split() -> None:
    """Слишком длинный раздел режется на части, но не по середине смысла."""
    paragraph = "Предложение номер один. Предложение номер два. " * 200
    md = f"# Большой раздел\n\n{paragraph}"
    chunks = chunk_markdown(md, file="big.md")
    assert len(chunks) > 1
    # Все части — из одного раздела
    assert all(c.section == "Большой раздел" for c in chunks)
    # Ни одна часть не превышает лимит
    from core.configs.rag_config import rag_settings

    assert all(len(c.text) <= rag_settings.MAX_CHUNK_CHARS + 200 for c in chunks)