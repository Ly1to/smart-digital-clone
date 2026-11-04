from __future__ import annotations

from datetime import UTC, datetime, time


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
