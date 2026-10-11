"""Базовый вызов LLM со structured output (Pydantic-схема) + retry/fallback."""

from typing import TypeVar

from loguru import logger
from pydantic import BaseModel

from llm.client import LLMClient

T = TypeVar("T", bound=BaseModel)


class AgentError(RuntimeError):
    """Агент не вернул валидную структуру."""


async def generate_structured(
    llm: LLMClient,
    schema: type[T],
    system_prompt: str,
    user_content: str,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> T:
    """Вызвать LLM и вернуть объект схемы (валидация и фолбэк на уровне клиента)."""
    runnable = llm.structured(
        schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    result = await runnable.ainvoke([("system", system_prompt), ("user", user_content)])
    if not isinstance(result, schema):
        raise AgentError(
            f"Агент вернул {type(result).__name__} вместо {schema.__name__}: {result!r}"
        )
    logger.debug("Structured output получен: schema={}", schema.__name__)
    return result