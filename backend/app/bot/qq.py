from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.bot import binding
from app.bot.exceptions import (
    BotNotConfiguredError,
    BotResponseError,
    BotUpstreamError,
    QQAlreadyBoundError,
)
from app.bot.llm import LLMProvider, get_llm_provider
from app.bot.pipeline import run_chat
from app.core.config import settings

logger = logging.getLogger(__name__)

BIND_PATTERN = re.compile(r"^/?(?:绑定|bind)\s*(\d{6})$", re.IGNORECASE)
COMMAND_PREFIX = "/日程"
MAX_INPUT_LENGTH = 2000

HELP_TEXT = "可以直接问我：今天有什么安排？本周还有哪些日程？搜索「项目」。"
UNBOUND_HINT = (
    "这个 QQ 还没有绑定日程账号。请在网页「账号」区域生成绑定码，然后私聊发送：绑定 123456"
)
GROUP_BIND_HINT = "绑定码请在私聊中发送，不要在群里暴露。"
BIND_INVALID = "绑定码无效或已过期，请重新在网页生成。"
BIND_SUCCESS = f"绑定成功。{HELP_TEXT}"
PROVIDER_MISSING = "助手还没有配置模型 API Key，请联系管理员。"
UPSTREAM_ERROR = "模型服务暂时不可用，请稍后再试。"


@dataclass(slots=True)
class QQReply:
    message_type: str
    target_id: int
    text: str


async def handle_event(
    db: Session,
    event: dict[str, Any],
    *,
    provider: LLMProvider | None = None,
) -> QQReply | None:
    """处理一条 OneBot 消息事件，返回要发送的回复。"""
    if event.get("post_type") != "message":
        return None
    message_type = event.get("message_type")
    if message_type not in {"private", "group"}:
        return None

    self_id = event.get("self_id")
    raw_user_id = event.get("user_id")
    if raw_user_id is None or str(raw_user_id) == str(self_id):
        return None
    try:
        qq_id = int(raw_user_id)
    except TypeError, ValueError:
        return None

    if message_type == "group":
        raw_group_id = event.get("group_id")
        if raw_group_id is None:
            return None
        try:
            group_id = int(raw_group_id)
        except TypeError, ValueError:
            return None
        if not _allowed_group(group_id):
            return None
        if not _mentions_self(event):
            return None
        target_id = group_id
    else:
        if not _allowed_user(qq_id):
            return None
        target_id = qq_id

    text = _strip_command_prefix(_message_text(event))
    bind_match = BIND_PATTERN.match(text)
    if bind_match:
        if message_type == "group":
            return QQReply(message_type, target_id, GROUP_BIND_HINT)
        return QQReply(message_type, target_id, _handle_bind(db, qq_id, bind_match.group(1)))

    if not text:
        return QQReply(message_type, target_id, HELP_TEXT)
    if len(text) > MAX_INPUT_LENGTH:
        text = text[:MAX_INPUT_LENGTH]

    linked = binding.get_binding(db, external_id=str(qq_id))
    if linked is None:
        return QQReply(message_type, target_id, UNBOUND_HINT)

    try:
        if provider is None:
            provider = get_llm_provider()
        reply_text, _ = await run_chat(
            db,
            user_id=linked.user_id,
            message=text,
            conversation_key=f"qq:{qq_id}",
            provider=provider,
        )
    except BotNotConfiguredError:
        reply_text = PROVIDER_MISSING
    except (BotUpstreamError, BotResponseError) as exc:
        logger.warning("QQ 对话失败：%s", exc)
        reply_text = UPSTREAM_ERROR

    return QQReply(message_type, target_id, reply_text)


def _handle_bind(db: Session, qq_id: int, code: str) -> str:
    user_id = binding.consume_bind_code(code)
    if user_id is None:
        return BIND_INVALID
    try:
        binding.bind_account(db, user_id=user_id, external_id=str(qq_id))
    except QQAlreadyBoundError as exc:
        return str(exc)
    return BIND_SUCCESS


def _message_text(event: dict[str, Any]) -> str:
    segments = event.get("message")
    if isinstance(segments, list):
        parts: list[str] = []
        for segment in segments:
            if not isinstance(segment, dict) or segment.get("type") != "text":
                continue
            data = segment.get("data")
            if isinstance(data, dict):
                parts.append(str(data.get("text") or ""))
        return "".join(parts).strip()
    raw = event.get("raw_message")
    if isinstance(raw, str):
        return raw.strip()
    return ""


def _strip_command_prefix(text: str) -> str:
    text = text.strip()
    if text.startswith(COMMAND_PREFIX):
        return text[len(COMMAND_PREFIX) :].strip()
    return text


def _mentions_self(event: dict[str, Any]) -> bool:
    self_id = event.get("self_id")
    if self_id is None:
        return False
    segments = event.get("message")
    if isinstance(segments, list):
        for segment in segments:
            if not isinstance(segment, dict) or segment.get("type") != "at":
                continue
            data = segment.get("data")
            if isinstance(data, dict) and str(data.get("qq")) == str(self_id):
                return True
    raw = event.get("raw_message")
    return isinstance(raw, str) and f"[CQ:at,qq={self_id}]" in raw


def _allowed_user(qq_id: int) -> bool:
    allowed = _parse_ids(settings.qq_bot_allowed_users)
    return not allowed or qq_id in allowed


def _allowed_group(group_id: int) -> bool:
    allowed = _parse_ids(settings.qq_bot_allowed_groups)
    return not allowed or group_id in allowed


def _parse_ids(raw: str) -> set[int]:
    values: set[int] = set()
    for part in raw.replace("，", ",").split(","):
        part = part.strip()
        if part.isdigit():
            values.add(int(part))
    return values
