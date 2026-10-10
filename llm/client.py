from collections.abc import AsyncIterator
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from core.configs.llm_config import llm_settings
from llm.schemas import ChatMessage, LLMResponse, to_chat_messages


def _to_lc_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
    from langchain_core.messages import (
        AIMessage as _AIMessage,
    )
    from langchain_core.messages import (
        HumanMessage,
        SystemMessage,
        ToolMessage,
    )

    mapping = {
        "system": SystemMessage,
        "user": HumanMessage,
        "assistant": _AIMessage,
        "tool": ToolMessage,
    }
    return [mapping[m.role](content=m.content) for m in messages]


class LLMClient:
    def __init__(self, model: str | None = None) -> None:
        self._primary_model = model or llm_settings.MODEL
        self._fallback_model = llm_settings.FALLBACK_MODEL or None

        common_kwargs = {
            "base_url": llm_settings.BASE_URL,
            "api_key": llm_settings.API_KEY or "EMPTY", 
            "temperature": llm_settings.TEMPERATURE,
            "max_tokens": llm_settings.MAX_TOKENS,
            "timeout": llm_settings.TIMEOUT_SECONDS,
            "max_retries": llm_settings.MAX_RETRIES,
        }
        self._primary = ChatOpenAI(model=self._primary_model, **common_kwargs)
        self._fallback = (
            ChatOpenAI(model=self._fallback_model, **common_kwargs)
            if self._fallback_model
            else None
        )
        logger.info(
            "LLM client initialized: model={model} base_url={base_url}"
            + (" fallback={fallback}" if self._fallback else ""),
            model=self._primary_model,
            base_url=llm_settings.BASE_URL,
            fallback=self._fallback_model,
        )

    async def chat(
        self,
        messages: list[ChatMessage | dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        chat_messages = to_chat_messages(messages)
        lc_messages = _to_lc_messages(chat_messages)

        overrides = {}
        if temperature is not None:
            overrides["temperature"] = temperature
        if max_tokens is not None:
            overrides["max_tokens"] = max_tokens

        try:
            return await self._invoke(self._primary, lc_messages, overrides)
        except Exception as exc:
            if self._fallback is None:
                raise
            logger.warning(
                "Primary LLM model '{}' failed ({}), falling back to '{}'",
                self._primary_model,
                exc,
                self._fallback_model,
            )
            return await self._invoke(self._fallback, lc_messages, overrides)

    async def chat_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        **kwargs: object,
    ) -> LLMResponse:
        messages: list[ChatMessage] = []
        if system:
            messages.append(ChatMessage(role="system", content=system))
        messages.append(ChatMessage(role="user", content=prompt))
        return await self.chat(messages, **kwargs) 

    async def stream(
        self,
        messages: list[ChatMessage | dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        chat_messages = to_chat_messages(messages)
        lc_messages = _to_lc_messages(chat_messages)

        target = self._primary
        if model:
            target = ChatOpenAI(
                model=model,
                base_url=llm_settings.BASE_URL,
                api_key=llm_settings.API_KEY or "EMPTY",
                temperature=temperature if temperature is not None else llm_settings.TEMPERATURE,
                max_tokens=max_tokens if max_tokens is not None else llm_settings.MAX_TOKENS,
                timeout=llm_settings.TIMEOUT_SECONDS,
                max_retries=llm_settings.MAX_RETRIES,
            )

        overrides = {}
        if temperature is not None:
            overrides["temperature"] = temperature
        if max_tokens is not None:
            overrides["max_tokens"] = max_tokens
        if overrides:
            target = target.bind(**overrides)

        async for chunk in target.astream(lc_messages):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield str(chunk.content)

    async def _invoke(
        self,
        client: ChatOpenAI,
        lc_messages: list[BaseMessage],
        overrides: dict[str, object],
    ) -> LLMResponse:
        result = await client.ainvoke(lc_messages, **overrides)
        assert isinstance(result, AIMessage)
        usage = getattr(result, "usage_metadata", None) or {}
        response = LLMResponse(
            content=result.text,
            model=result.response_metadata.get("model_name", ""),
            finish_reason=result.response_metadata.get("finish_reason"),
            tokens_in=int(usage.get("input_tokens", 0)),
            tokens_out=int(usage.get("output_tokens", 0)),
            raw=result,
        )
        logger.debug(
            "LLM response: model={} tokens_in={} tokens_out={}",
            response.model,
            response.tokens_in,
            response.tokens_out,
        )
        return response


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
