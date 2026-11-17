from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from typing import Any

from app.bot.llm import get_llm_provider
from app.core.config import settings
from app.core.time import app_timezone, local_now
from app.main import app


class ScriptedProvider:
    """按脚本返回预设回复，用来替代真实 DeepSeek 请求。"""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls: list[list[dict[str, Any]]] = []

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.calls.append([dict(message) for message in messages])
        assert self._responses, "没有更多预设回复"
        return self._responses.pop(0)


def _today_bounds() -> tuple[datetime, datetime]:
    tz = app_timezone()
    start = datetime.combine(local_now().date(), time.min, tzinfo=tz)
    return start, start + timedelta(days=1)


def _tool_call(call_id: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)},
    }


def _create_today_schedule(client) -> None:
    start = datetime.combine(local_now().date(), time(10, 0), tzinfo=app_timezone())
    response = client.post(
        "/api/schedules",
        json={
            "title": "机器人测试日程",
            "category": "work",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
        },
    )
    assert response.status_code == 201, response.text


def _use_provider(fake: ScriptedProvider) -> None:
    app.dependency_overrides[get_llm_provider] = lambda: fake


def test_bot_chat_runs_schedule_tool(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "bot_history_turns", 6)
    _create_today_schedule(client)
    start, end = _today_bounds()
    fake = ScriptedProvider(
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    _tool_call(
                        "call_1",
                        "list_schedules",
                        {"start": start.isoformat(), "end": end.isoformat()},
                    )
                ],
            },
            {"role": "assistant", "content": "今天有一个工作日程。", "tool_calls": None},
        ]
    )
    _use_provider(fake)

    response = client.post("/api/bot/chat", json={"message": "我今天有什么安排"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["reply"] == "今天有一个工作日程。"
    assert data["tools_used"] == ["list_schedules"]
    assert data["conversation_id"]
    tool_message = fake.calls[1][-1]
    assert tool_message["role"] == "tool"
    assert "机器人测试日程" in tool_message["content"]


def test_bot_chat_keeps_conversation_history(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "bot_history_turns", 6)
    fake = ScriptedProvider(
        [
            {"role": "assistant", "content": "第一轮回复", "tool_calls": None},
            {"role": "assistant", "content": "第二轮回复", "tool_calls": None},
        ]
    )
    _use_provider(fake)

    first = client.post(
        "/api/bot/chat",
        json={"message": "第一轮问题", "conversation_id": "history-case"},
    )
    second = client.post(
        "/api/bot/chat",
        json={"message": "第二轮问题", "conversation_id": "history-case"},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["reply"] == "第二轮回复"
    assert {"role": "user", "content": "第一轮问题"} in fake.calls[1]
    assert {"role": "assistant", "content": "第一轮回复"} in fake.calls[1]
    assert fake.calls[1][-1] == {"role": "user", "content": "第二轮问题"}


def test_bot_chat_requires_api_key(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "deepseek_api_key", "")

    response = client.post("/api/bot/chat", json={"message": "你好"})

    assert response.status_code == 503
    assert "DEEPSEEK_API_KEY" in response.json()["detail"]


def test_bot_status_reports_configuration(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")
    monkeypatch.setattr(settings, "deepseek_model", "deepseek-chat")
    monkeypatch.setattr(settings, "qq_bot_enabled", False)

    response = client.get("/api/bot/status")

    assert response.status_code == 200
    assert response.json() == {
        "configured": True,
        "provider": "deepseek",
        "model": "deepseek-chat",
        "qq_enabled": False,
        "qq_connected": False,
    }


def test_bot_chat_requires_login(anonymous_client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")

    response = anonymous_client.post("/api/bot/chat", json={"message": "你好"})

    assert response.status_code == 401
