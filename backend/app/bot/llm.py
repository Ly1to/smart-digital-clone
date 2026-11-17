from __future__ import annotations

import logging
from typing import Any, Protocol

import httpx

from app.bot.exceptions import (
    BotNotConfiguredError,
    BotResponseError,
    BotUpstreamError,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

ChatMessage = dict[str, Any]
ToolSpec = dict[str, Any]


class LLMProvider(Protocol):
    async def chat(self, messages: list[ChatMessage], tools: list[ToolSpec]) -> ChatMessage:
        """发送一轮对话，返回 assistant 消息（content 或 tool_calls）。"""
        ...


def get_llm_provider() -> LLMProvider:
    """FastAPI 依赖：按配置创建 Provider，未配置时给出明确错误。"""
    api_key = settings.deepseek_api_key.strip()
    if not api_key:
        raise BotNotConfiguredError()
    return DeepSeekProvider(
        api_key=api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.bot_llm_timeout_seconds,
    )


class DeepSeekProvider:
    """DeepSeek 的 OpenAI 兼容 Chat Completions 实现。

    其他兼容 OpenAI 协议的服务也可以通过 DEEPSEEK_BASE_URL / DEEPSEEK_MODEL 复用。
    """

    def __init__(self, *, api_key: str, base_url: str, model: str, timeout: float) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def chat(self, messages: list[ChatMessage], tools: list[ToolSpec]) -> ChatMessage:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.2,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            logger.warning("DeepSeek 请求失败：%s", exc)
            raise BotUpstreamError("无法连接对话模型服务，请稍后再试") from exc

        if response.status_code >= 400:
            raise BotUpstreamError(self._error_message(response))

        try:
            data = response.json()
        except ValueError as exc:
            raise BotResponseError("对话模型返回了无法解析的响应") from exc

        choices = data.get("choices") if isinstance(data, dict) else None
        if not isinstance(choices, list) or not choices:
            raise BotResponseError("对话模型没有返回结果")

        choice = choices[0]
        message = choice.get("message") if isinstance(choice, dict) else None
        if not isinstance(message, dict):
            raise BotResponseError("对话模型返回格式不正确")

        content = message.get("content") or ""
        if not isinstance(content, str):
            content = str(content)

        tool_calls = message.get("tool_calls")
        if tool_calls is not None:
            if not isinstance(tool_calls, list):
                raise BotResponseError("对话模型返回的工具调用格式不正确")
            tool_calls = [call for call in tool_calls if isinstance(call, dict)] or None

        if not content and not tool_calls:
            raise BotResponseError("对话模型返回了空内容")

        return {"role": "assistant", "content": content, "tool_calls": tool_calls}

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        detail = ""
        try:
            payload = response.json()
            error = payload.get("error") if isinstance(payload, dict) else None
            if isinstance(error, dict):
                detail = str(error.get("message") or "")
            elif isinstance(error, str):
                detail = error
        except ValueError:
            detail = response.text[:200]
        if detail:
            return f"对话模型服务返回 {response.status_code}：{detail}"
        return f"对话模型服务返回 {response.status_code}"
