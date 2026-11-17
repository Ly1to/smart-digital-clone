from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from websockets.asyncio.client import ClientConnection, connect

from app.bot.qq import QQReply, handle_event
from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


@dataclass
class ConnectionState:
    connected: bool = False
    last_error: str = ""


STATE = ConnectionState()


def is_connected() -> bool:
    return STATE.connected


async def run_qq_bot() -> None:
    """连接 NapCat 的 OneBot v11 WebSocket，断线后指数退避重连。"""
    url = settings.onebot_ws_url.strip()
    if not url:
        logger.warning("QQ_BOT_ENABLED=true 但未配置 ONEBOT_WS_URL，跳过 QQ 接入")
        return

    delay = 5.0
    while True:
        try:
            async with connect(
                url,
                additional_headers=_headers(),
                max_size=8 * 1024 * 1024,
            ) as ws:
                STATE.connected = True
                STATE.last_error = ""
                delay = 5.0
                logger.info("OneBot WebSocket 已连接：%s", url)
                async for raw in ws:
                    if isinstance(raw, (str, bytes)):
                        await _dispatch(ws, raw)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - 连接异常需要重试而不是退出进程
            STATE.last_error = str(exc)
            logger.warning("OneBot 连接失败：%s，%s 秒后重试", exc, int(delay))
        finally:
            STATE.connected = False
        await asyncio.sleep(delay)
        delay = min(delay * 2, 60)


async def _dispatch(ws: ClientConnection, raw: str | bytes) -> None:
    try:
        event = json.loads(raw)
    except json.JSONDecodeError, TypeError:
        return
    if not isinstance(event, dict) or event.get("post_type") != "message":
        return

    try:
        with SessionLocal() as db:
            reply = await handle_event(db, event)
    except Exception:  # noqa: BLE001 - 单条消息失败不应断开连接
        logger.exception("处理 QQ 消息失败")
        return

    if reply is not None:
        await send_reply(ws, reply)


async def send_reply(ws: ClientConnection, reply: QQReply) -> None:
    if reply.message_type == "group":
        action = "send_group_msg"
        params: dict[str, Any] = {"group_id": reply.target_id}
    else:
        action = "send_private_msg"
        params = {"user_id": reply.target_id}

    for chunk in split_message(reply.text, settings.qq_bot_reply_chunk_size):
        await ws.send(
            json.dumps(
                {
                    "action": action,
                    "params": {**params, "message": chunk, "auto_escape": True},
                },
                ensure_ascii=False,
            )
        )


def split_message(text: str, size: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [text[index : index + size] for index in range(0, len(text), size)]


def _headers() -> dict[str, str] | None:
    token = settings.onebot_access_token.strip()
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}
