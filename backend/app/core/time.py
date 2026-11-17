from __future__ import annotations

from datetime import UTC, datetime, time
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.core.config import settings


@lru_cache
def app_timezone() -> ZoneInfo:
    """应用时区，由 APP_TIMEZONE 配置，用于自动排程的日期边界。"""
    return ZoneInfo(settings.app_timezone)


def local_now() -> datetime:
    """当前时间，带应用时区，不依赖容器或宿主机 TZ 环境变量。"""
    return datetime.now(app_timezone())


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_utc(value: datetime) -> datetime:
    """无时区时间按 UTC 处理，有时区时间转换为 UTC。"""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def normalize_all_day(start_at: datetime, end_at: datetime) -> tuple[datetime, datetime]:
    """全天事件按日期存储：开始日 00:00 UTC 到结束日 23:59:59.999999 UTC，首尾日期都包含。"""
    start_date = to_utc(start_at).date()
    end_date = to_utc(end_at).date()
    return (
        datetime.combine(start_date, time.min, tzinfo=UTC),
        datetime.combine(end_date, time.max, tzinfo=UTC),
    )


def serialize_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    value = to_utc(value)
    return value.isoformat().replace("+00:00", "Z")
