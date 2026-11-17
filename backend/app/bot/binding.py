from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.bot.exceptions import QQAlreadyBoundError
from app.core.config import settings
from app.models.qq_binding import QqBinding

PLATFORM = "onebot"


@dataclass(slots=True)
class BindCode:
    code: str
    expires_at: datetime


# 绑定码只保存在进程内，短期有效；重启后失效是可接受的。
_lock = threading.Lock()
_codes: dict[str, tuple[int, datetime]] = {}


def create_bind_code(user_id: int, *, ttl_seconds: int | None = None) -> BindCode:
    ttl = settings.qq_bind_code_ttl_seconds if ttl_seconds is None else ttl_seconds
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=ttl)
    with _lock:
        _purge_locked(now)
        for _ in range(20):
            code = str(secrets.randbelow(900000) + 100000)
            if code not in _codes:
                _codes[code] = (user_id, expires_at)
                return BindCode(code=code, expires_at=expires_at)
    raise RuntimeError("无法生成绑定码，请稍后重试")


def consume_bind_code(code: str) -> int | None:
    """一次性消费绑定码，返回对应的 user_id。"""
    now = datetime.now(UTC)
    with _lock:
        _purge_locked(now)
        entry = _codes.pop(code.strip(), None)
    if entry is None:
        return None
    user_id, expires_at = entry
    if expires_at <= now:
        return None
    return user_id


def clear_bind_codes() -> None:
    """测试辅助：清空内存中的绑定码。"""
    with _lock:
        _codes.clear()


def _purge_locked(now: datetime) -> None:
    expired = [code for code, (_, expires_at) in _codes.items() if expires_at <= now]
    for code in expired:
        _codes.pop(code, None)


def get_binding(
    db: Session,
    *,
    external_id: str,
    platform: str = PLATFORM,
) -> QqBinding | None:
    return db.scalar(
        select(QqBinding).where(
            QqBinding.platform == platform,
            QqBinding.external_id == external_id,
        )
    )


def list_bindings(db: Session, user_id: int) -> list[QqBinding]:
    return list(
        db.scalars(
            select(QqBinding)
            .where(QqBinding.user_id == user_id)
            .order_by(QqBinding.created_at.asc(), QqBinding.id.asc())
        )
    )


def bind_account(
    db: Session,
    *,
    user_id: int,
    external_id: str,
    platform: str = PLATFORM,
) -> QqBinding:
    external_id = external_id.strip()
    if not external_id:
        raise ValueError("QQ 号不能为空")

    existing = get_binding(db, external_id=external_id, platform=platform)
    if existing is not None:
        if existing.user_id == user_id:
            return existing
        raise QQAlreadyBoundError()

    binding = QqBinding(user_id=user_id, platform=platform, external_id=external_id)
    db.add(binding)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise QQAlreadyBoundError() from exc
    db.refresh(binding)
    return binding


def delete_binding(db: Session, *, user_id: int, binding_id: int) -> bool:
    binding = db.scalar(
        select(QqBinding).where(
            QqBinding.id == binding_id,
            QqBinding.user_id == user_id,
        )
    )
    if binding is None:
        return False
    db.delete(binding)
    db.commit()
    return True
