from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.bot.context import STORE, ConversationStore
from app.bot.exceptions import BotResponseError
from app.bot.llm import ChatMessage, LLMProvider
from app.bot.prompt import build_system_prompt
from app.bot.tools import TOOL_SPECS, execute_tool
from app.core.config import settings
from app.core.time import local_now


async def run_chat(
    db: Session,
    *,
    user_id: int,
    message: str,
    conversation_key: str,
    provider: LLMProvider,
    store: ConversationStore = STORE,
) -> tuple[str, list[str]]:
    """执行一轮对话，返回最终回复和本轮调用过的工具名。"""
    history = store.history(conversation_key) if settings.bot_history_turns > 0 else []
    messages: list[ChatMessage] = [
        {"role": "system", "content": build_system_prompt(local_now())},
        *history,
        {"role": "user", "content": message},
    ]
    tools_used: list[str] = []

    for _ in range(settings.bot_max_tool_rounds):
        assistant = await provider.chat(messages, TOOL_SPECS)
        tool_calls = assistant.get("tool_calls")
        if not tool_calls:
            reply = str(assistant.get("content") or "").strip()
            if not reply:
                raise BotResponseError("对话模型没有返回内容，请换一种问法")
            store.append(conversation_key, message, reply, settings.bot_history_turns)
            return reply, tools_used

        messages.append(
            {
                "role": "assistant",
                "content": str(assistant.get("content") or ""),
                "tool_calls": tool_calls,
            }
        )
        for call in tool_calls:
            function = call.get("function") if isinstance(call, dict) else None
            name = ""
            arguments: dict[str, Any] | None = None
            if isinstance(function, dict):
                name = str(function.get("name") or "")
                arguments = _parse_arguments(function.get("arguments"))
            if arguments is None:
                content = json.dumps({"error": "工具参数不是合法的 JSON 对象"}, ensure_ascii=False)
            else:
                content = execute_tool(db, user_id=user_id, name=name, arguments=arguments)
            tools_used.append(name)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": str(call.get("id") or name) if isinstance(call, dict) else name,
                    "content": content,
                }
            )

    raise BotResponseError("模型调用工具的次数过多，请换一种问法")


def _parse_arguments(raw: Any) -> dict[str, Any] | None:
    if raw in (None, ""):
        return {}
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
