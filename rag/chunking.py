import re
from loguru import logger
from core.configs.rag_config import rag_settings
from rag.schemas import Chunk

# Заголовки markdown: #, ##, ###, ...
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# Слишком короткие «разделы» (например, один заголовок без текста) — пропускаем.
_MIN_CHUNK_CHARS = rag_settings.MIN_CHUNK_CHARS
_MAX_CHUNK_CHARS = rag_settings.MAX_CHUNK_CHARS


def _split_long_block(text: str, section: str, file: str) -> list[str]:
    """Разбить слишком длинный блок на части по границам абзацев/предложений."""
    if len(text) <= _MAX_CHUNK_CHARS:
        return [text]

    parts: list[str] = []
    current = ""
    for paragraph in re.split(r"\n\s*\n", text):
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph.strip()
        if len(candidate) > _MAX_CHUNK_CHARS and current:
            parts.append(current)
            current = paragraph.strip()
        else:
            current = candidate
        if len(current) > _MAX_CHUNK_CHARS:
            # Один гигантский абзац — режем по предложениям.
            for sentence in re.split(r"(?<=[.!?])\s+", current):
                if len(parts) and len(parts[-1]) + len(sentence) <= _MAX_CHUNK_CHARS:
                    parts[-1] = f"{parts[-1]} {sentence}"
                else:
                    parts.append(sentence)
            current = ""
    if current:
        parts.append(current)
    return [p for p in parts if p.strip()]


def chunk_markdown(
    markdown: str,
    *,
    file: str,
    source_type: str = "document",
    date: str | None = None,
) -> list[Chunk]:
    """Разбить markdown на структурные чанки.

    Каждый чанк соответствует разделу/подразделу документа. Текст до первого
    заголовка считается «введением» (section=""). Метаданные чанка: file,
    section, source_type, date.
    """
    lines = markdown.splitlines()
    chunks: list[Chunk] = []
    current_section = ""
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines
        text = "\n".join(current_lines).strip()
        current_lines = []
        if not text:
            return
        for part in _split_long_block(text, current_section, file):
            if len(part) < _MIN_CHUNK_CHARS:
                continue
            chunks.append(
                Chunk(
                    text=part,
                    file=file,
                    section=current_section,
                    source_type=source_type,
                    date=date,
                )
            )

    for line in lines:
        match = _HEADING_RE.match(line)
        if match:
            flush()
            current_section = match.group(2).strip()
            continue
        current_lines.append(line)

    flush()
    logger.debug(
        "Чанкинг: file={} chunks={} (source_type={})", file, len(chunks), source_type
    )
    return chunks