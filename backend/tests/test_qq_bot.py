from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from app.bot import binding, context
from app.bot.onebot import send_reply, split_message
from app.bot.qq import QQReply, handle_event
from app.core.config import settings
from app.models.user import User


@pytest.fixture(autouse=True)
def reset_bot_state() -> None:
    binding.clear_bind_codes()
    context.STORE.clear()
    yield
    binding.clear_bind_codes()
    context.STORE.clear()


class ScriptedProvider:
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


def _event(
    message_type: str,
    user_id: int,
    text: str,
    *,
    group_id: int | None = None,
    self_id: int = 10000,
    mention: bool = False,
) -> dict[str, Any]:
    segments: list[dict[str, Any]] = []
    if mention:
        segments.append({"type": "at", "data": {"qq": str(self_id)}})
    segments.append({"type": "text", "data": {"text": text}})
    event: dict[str, Any] = {
        "post_type": "message",
        "message_type": message_type,
        "self_id": self_id,
        "user_id": user_id,
        "raw_message": text,
        "message": segments,
    }
    if group_id is not None:
        event["group_id"] = group_id
    return event


def _run(db, event: dict[str, Any], provider=None):
    return asyncio.run(handle_event(db, event, provider=provider))


def test_bind_code_binds_qq_via_private_message(client, db, test_user) -> None:
    response = client.post("/api/bot/bind-code")

    assert response.status_code == 201
    data = response.json()
    assert len(data["code"]) == 6
    assert data["expires_in_seconds"] == 600

    reply = _run(db, _event("private", 123456, f"绑定 {data['code']}"))

    assert reply is not None
    assert "绑定成功" in reply.text
    linked = binding.get_binding(db, external_id="123456")
    assert linked is not None
    assert linked.user_id == test_user.id
    assert binding.consume_bind_code(data["code"]) is None


def test_bind_code_cannot_take_over_another_account(client, db, test_user) -> None:
    other = User(username="other", password_hash="unused")
    db.add(other)
    db.commit()
    db.refresh(other)
    binding.bind_account(db, user_id=test_user.id, external_id="555555")

    code = client.post("/api/bot/bind-code").json()["code"]
    # 让绑定码属于另一个账号，验证同一 QQ 不能被抢占。
    binding.clear_bind_codes()
    other_code = binding.create_bind_code(other.id).code

    reply = _run(db, _event("private", 555555, f"绑定 {other_code}"))

    assert code != other_code
    assert reply is not None
    assert "已绑定其他账号" in reply.text
    linked = binding.get_binding(db, external_id="555555")
    assert linked is not None
    assert linked.user_id == test_user.id


def test_unbound_qq_gets_binding_hint(db) -> None:
    reply = _run(db, _event("private", 777777, "今天有什么安排"))

    assert reply is not None
    assert "没有绑定" in reply.text


def test_bound_qq_chats_with_provider(db, test_user) -> None:
    binding.bind_account(db, user_id=test_user.id, external_id="888888")
    fake = ScriptedProvider(
        [{"role": "assistant", "content": "今天没有安排。", "tool_calls": None}]
    )

    reply = _run(db, _event("private", 888888, "今天有什么安排"), provider=fake)

    assert reply is not None
    assert reply.message_type == "private"
    assert reply.target_id == 888888
    assert reply.text == "今天没有安排。"
    assert len(fake.calls) == 1


def test_group_message_requires_mention(db, test_user) -> None:
    binding.bind_account(db, user_id=test_user.id, external_id="999999")
    fake = ScriptedProvider(
        [{"role": "assistant", "content": "本周有一个日程。", "tool_calls": None}]
    )

    ignored = _run(db, _event("group", 999999, "今天有什么安排", group_id=42), provider=fake)
    assert ignored is None

    reply = _run(
        db,
        _event("group", 999999, "今天有什么安排", group_id=42, mention=True),
        provider=fake,
    )
    assert reply is not None
    assert reply.message_type == "group"
    assert reply.target_id == 42


def test_qq_whitelist_blocks_unlisted_user(db, test_user, monkeypatch) -> None:
    monkeypatch.setattr(settings, "qq_bot_allowed_users", "111111")
    binding.bind_account(db, user_id=test_user.id, external_id="222222")

    reply = _run(db, _event("private", 222222, "今天有什么安排"))

    assert reply is None


def test_bind_code_expires(test_user) -> None:
    result = binding.create_bind_code(test_user.id, ttl_seconds=-1)

    assert binding.consume_bind_code(result.code) is None


def test_binding_api_lists_and_deletes(client, db, test_user) -> None:
    code = client.post("/api/bot/bind-code").json()["code"]
    _run(db, _event("private", 321321, f"绑定 {code}"))

    listed = client.get("/api/bot/bindings")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["external_id"] == "321321"

    deleted = client.delete(f"/api/bot/bindings/{listed.json()[0]['id']}")
    assert deleted.status_code == 204
    assert client.get("/api/bot/bindings").json() == []
    assert binding.get_binding(db, external_id="321321") is None


def test_split_message_chunks_long_text() -> None:
    assert split_message("abcdef", 2) == ["ab", "cd", "ef"]
    assert split_message("   ", 10) == []


class FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send(self, payload: str) -> None:
        self.sent.append(json.loads(payload))


def test_send_reply_uses_onebot_actions(monkeypatch) -> None:
    monkeypatch.setattr(settings, "qq_bot_reply_chunk_size", 3)
    private_ws = FakeWebSocket()
    asyncio.run(send_reply(private_ws, QQReply("private", 123, "abcdef")))

    assert [item["action"] for item in private_ws.sent] == [
        "send_private_msg",
        "send_private_msg",
    ]
    assert private_ws.sent[0]["params"]["user_id"] == 123
    assert private_ws.sent[0]["params"]["message"] == "abc"

    group_ws = FakeWebSocket()
    asyncio.run(send_reply(group_ws, QQReply("group", 456, "hi")))

    assert group_ws.sent[0]["action"] == "send_group_msg"
    assert group_ws.sent[0]["params"]["group_id"] == 456
