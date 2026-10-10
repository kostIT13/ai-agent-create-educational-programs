from typing import Any, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):

    role: Literal["system", "user", "assistant", "tool"]
    content: str


class LLMResponse(BaseModel):

    content: str
    model: str = ""
    finish_reason: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    raw: Any = Field(default=None, exclude=True, repr=False)


def to_chat_messages(messages: list[ChatMessage | dict[str, str]]) -> list[ChatMessage]:
    result: list[ChatMessage] = []
    for msg in messages:
        if isinstance(msg, ChatMessage):
            result.append(msg)
        else:
            result.append(ChatMessage.model_validate(msg))
    return result
