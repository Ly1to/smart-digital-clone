from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, time, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.time import app_timezone, local_now, to_utc
from app.models.enums import (
    CATEGORY_LABELS,
    STATUS_LABELS,
    ScheduleCategory,
    ScheduleStatus,
)
from app.models.schedule import Schedule
from app.services import schedule_service
from app.services.exceptions import ScheduleNotFoundError

logger = logging.getLogger(__name__)

MAX_ITEMS = 50
SEARCH_LIMIT = 20
MAX_RANGE = timedelta(days=366)

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_schedules",
            "description": (
                "查询指定时间区间内的日程。start 和 end 需要成对提供；"
                "都不提供时默认查询今天。时间为 ISO 8601，不带时区时按应用时区解释。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "开始时间，ISO 8601，包含，例如 2026-11-17T00:00:00+08:00",
                    },
                    "end": {
                        "type": "string",
                        "description": "结束时间，ISO 8601，不包含，例如 2026-11-18T00:00:00+08:00",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["work", "outing", "private"]},
                        "description": "按分类过滤，留空表示全部分类",
                    },
                    "statuses": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["pending", "completed", "cancelled"],
                        },
                        "description": "按状态过滤，留空表示全部状态",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_schedules",
            "description": "按关键词搜索日程的标题和描述，返回匹配的日程列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "要搜索的关键词"},
                },
                "required": ["keyword"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": "按 ID 查询一条日程的完整信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "integer", "description": "日程 ID"},
                },
                "required": ["schedule_id"],
                "additionalProperties": False,
            },
        },
    },
]


def execute_tool(db: Session, *, user_id: int, name: str, arguments: dict[str, Any]) -> str:
    """执行工具并返回给模型的 JSON 字符串；业务错误也作为结果返回。"""
    try:
        if name == "list_schedules":
            return _list_schedules(db, user_id, arguments)
        if name == "search_schedules":
            return _search_schedules(db, user_id, arguments)
        if name == "get_schedule":
            return _get_schedule(db, user_id, arguments)
        return _error(f"未知工具：{name}")
    except (ValueError, ScheduleNotFoundError) as exc:
        return _error(str(exc))
    except Exception:  # noqa: BLE001 - 工具异常不应打断整轮对话
        logger.exception("对话工具执行失败：%s", name)
        return _error("工具执行失败，请稍后再试")


def _list_schedules(db: Session, user_id: int, arguments: dict[str, Any]) -> str:
    start_raw = arguments.get("start")
    end_raw = arguments.get("end")
    if (start_raw is None) != (end_raw is None):
        raise ValueError("start 和 end 需要同时提供，或都不提供以查询今天")

    if start_raw is None:
        start, end = _today_range()
    else:
        start = _parse_datetime(start_raw, "start")
        end = _parse_datetime(end_raw, "end")
        if end <= start:
            raise ValueError("end 必须晚于 start")
        if end - start > MAX_RANGE:
            raise ValueError("查询范围过大，请缩小到一年以内")

    schedules = schedule_service.list_schedules(
        db,
        user_id=user_id,
        start=start,
        end=end,
        categories=_parse_categories(arguments.get("categories")),
        statuses=_parse_statuses(arguments.get("statuses")),
    )
    return _result(schedules, limit=MAX_ITEMS)


def _search_schedules(db: Session, user_id: int, arguments: dict[str, Any]) -> str:
    keyword = arguments.get("keyword")
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError("keyword 不能为空")
    schedules = schedule_service.list_schedules(
        db,
        user_id=user_id,
        keyword=keyword.strip(),
    )
    return _result(schedules, limit=SEARCH_LIMIT)


def _get_schedule(db: Session, user_id: int, arguments: dict[str, Any]) -> str:
    schedule_id = arguments.get("schedule_id")
    if isinstance(schedule_id, bool) or not isinstance(schedule_id, int):
        raise ValueError("schedule_id 必须是整数")
    schedule = schedule_service.get_schedule(db, schedule_id, user_id)
    return json.dumps({"schedule": _format_schedule(schedule)}, ensure_ascii=False)


def _today_range() -> tuple[datetime, datetime]:
    tz = app_timezone()
    start = datetime.combine(local_now().date(), time.min, tzinfo=tz)
    return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)


def _parse_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} 必须是 ISO 8601 时间字符串")
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} 不是有效的 ISO 8601 时间：{value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=app_timezone())
    return parsed.astimezone(UTC)


def _parse_categories(value: Any) -> list[ScheduleCategory] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("categories 必须是数组")
    try:
        return [ScheduleCategory(str(item)) for item in value]
    except ValueError as exc:
        raise ValueError("不支持的分类，可用值为 work、outing、private") from exc


def _parse_statuses(value: Any) -> list[ScheduleStatus] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("statuses 必须是数组")
    try:
        return [ScheduleStatus(str(item)) for item in value]
    except ValueError as exc:
        raise ValueError("不支持的状态，可用值为 pending、completed、cancelled") from exc


def _result(schedules: list[Schedule], *, limit: int) -> str:
    items = [_format_schedule(schedule) for schedule in schedules[:limit]]
    return json.dumps(
        {
            "total": len(schedules),
            "returned": len(items),
            "truncated": len(schedules) > limit,
            "timezone": str(app_timezone()),
            "items": items,
        },
        ensure_ascii=False,
    )


def _format_schedule(schedule: Schedule) -> dict[str, Any]:
    description = schedule.description
    if description and len(description) > 200:
        description = f"{description[:200]}…"
    return {
        "id": schedule.id,
        "title": schedule.title,
        "category": schedule.category.value,
        "category_label": CATEGORY_LABELS.get(schedule.category, schedule.category.value),
        "status": schedule.status.value,
        "status_label": STATUS_LABELS.get(schedule.status, schedule.status.value),
        "all_day": schedule.all_day,
        "start": _display_time(schedule.start_at, schedule.all_day),
        "end": _display_time(schedule.end_at, schedule.all_day),
        "location": schedule.location,
        "description": description,
        "source": schedule.source,
    }


def _display_time(value: datetime, all_day: bool) -> str:
    if all_day:
        # 全天日程按 UTC 日期分量读取，避免时区换算把日期挪一天。
        return to_utc(value).date().isoformat()
    return to_utc(value).astimezone(app_timezone()).isoformat(timespec="minutes")


def _error(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)
