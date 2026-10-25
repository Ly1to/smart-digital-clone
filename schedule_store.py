"""Persistent schedule objects for Orbit."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SCHEDULE_TYPES = ("work", "leisure", "personal")
SCHEDULE_STATUSES = ("planned", "done")
SCHEMA_VERSION = 2


class ScheduleError(ValueError):
    """Raised when schedule input or storage is invalid."""


class ScheduleNotFound(ScheduleError):
    """Raised when a requested schedule does not exist."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required_text(data: Mapping[str, Any], key: str, max_length: int) -> str:
    value = str(data.get(key) or "").strip()
    if not value:
        raise ScheduleError(f"字段 {key} 不能为空。")
    if len(value) > max_length:
        raise ScheduleError(f"字段 {key} 不能超过 {max_length} 个字符。")
    return value


def _optional_text(data: Mapping[str, Any], key: str, max_length: int) -> str:
    value = str(data.get(key) or "").strip()
    if len(value) > max_length:
        raise ScheduleError(f"字段 {key} 不能超过 {max_length} 个字符。")
    return value


def _optional_deadline(data: Mapping[str, Any]) -> str | None:
    value = data.get("deadline")
    if value is None or str(value).strip() == "":
        return None
    try:
        deadline = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError as error:
        raise ScheduleError(
            "字段 deadline 必须使用 ISO 日期时间，例如 2026-10-24T18:00。"
        ) from error
    return deadline.replace(second=0, microsecond=0).isoformat(timespec="minutes")


@dataclass(frozen=True)
class Schedule:
    id: str
    type: str
    title: str
    date: str
    start_time: str
    duration_minutes: int
    deadline: str | None = None
    description: str = ""
    status: str = "planned"
    featured: bool = False
    source: str = "manual"
    source_url: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
        *,
        allow_missing_id: bool = False,
    ) -> "Schedule":
        if not isinstance(data, Mapping):
            raise ScheduleError("日程必须是 JSON 对象。")

        schedule_id = str(data.get("id") or "").strip()
        if not schedule_id and allow_missing_id:
            schedule_id = f"sch_{uuid.uuid4().hex[:12]}"
        if not schedule_id:
            raise ScheduleError("字段 id 不能为空。")

        schedule_type = str(data.get("type") or "").strip().lower()
        if schedule_type not in SCHEDULE_TYPES:
            raise ScheduleError(
                f"字段 type 必须是以下值之一：{', '.join(SCHEDULE_TYPES)}。"
            )

        date_value = str(data.get("date") or "").strip()
        try:
            date.fromisoformat(date_value)
        except ValueError as error:
            raise ScheduleError("字段 date 必须使用 YYYY-MM-DD 格式。") from error

        start_time = str(data.get("startTime") or data.get("start_time") or "").strip()
        try:
            datetime.strptime(start_time, "%H:%M")
        except ValueError as error:
            raise ScheduleError("字段 startTime 必须使用 HH:MM 格式。") from error

        try:
            duration_minutes = int(
                data.get("durationMinutes") or data.get("duration_minutes")
            )
        except (TypeError, ValueError) as error:
            raise ScheduleError("字段 durationMinutes 必须是整数。") from error
        if not 1 <= duration_minutes <= 24 * 60:
            raise ScheduleError("字段 durationMinutes 必须在 1 到 1440 之间。")

        status = str(data.get("status") or "planned").strip().lower()
        if status not in SCHEDULE_STATUSES:
            raise ScheduleError(
                f"字段 status 必须是以下值之一：{', '.join(SCHEDULE_STATUSES)}。"
            )

        now = _utc_now()
        created_at = str(data.get("createdAt") or data.get("created_at") or now)
        updated_at = str(data.get("updatedAt") or data.get("updated_at") or now)
        return cls(
            id=schedule_id,
            type=schedule_type,
            title=_required_text(data, "title", 120),
            date=date_value,
            start_time=start_time,
            duration_minutes=duration_minutes,
            deadline=_optional_deadline(data),
            description=_optional_text(data, "description", 240),
            status=status,
            featured=bool(data.get("featured", False)),
            source=str(data.get("source") or "manual").strip() or "manual",
            source_url=str(
                data.get("sourceUrl") or data.get("source_url") or ""
            ).strip(),
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "date": self.date,
            "startTime": self.start_time,
            "durationMinutes": self.duration_minutes,
            "deadline": self.deadline,
            "description": self.description,
            "status": self.status,
            "featured": self.featured,
            "source": self.source,
            "sourceUrl": self.source_url,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def with_updates(self, updates: Mapping[str, Any]) -> "Schedule":
        merged = self.to_dict()
        allowed_fields = {
            "type",
            "title",
            "date",
            "startTime",
            "durationMinutes",
            "deadline",
            "description",
            "status",
            "featured",
            "source",
            "sourceUrl",
        }
        for key, value in updates.items():
            if key in allowed_fields:
                merged[key] = value
        merged["id"] = self.id
        merged["createdAt"] = self.created_at
        merged["updatedAt"] = _utc_now()
        return Schedule.from_dict(merged)


class ScheduleStore:
    """Thread-safe JSON-backed schedule store with atomic writes."""

    def __init__(self, path: str | Path, seed_path: str | Path | None = None):
        self.path = Path(path).expanduser().resolve()
        self.seed_path = (
            Path(seed_path).expanduser().resolve() if seed_path else None
        )
        self._lock = threading.RLock()
        with self._lock:
            if not self.path.exists():
                self._initialize()

    def _initialize(self) -> None:
        schedules: list[Schedule] = []
        if self.seed_path and self.seed_path.exists():
            for item in self._read_items(self.seed_path):
                schedule = Schedule.from_dict(item, allow_missing_id=True)
                schedules.append(schedule)
        self._write(schedules)

    @staticmethod
    def _read_items(path: Path) -> list[Mapping[str, Any]]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise ScheduleError(f"无法读取日程文件 {path}：{error}") from error
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = payload.get("items")
        else:
            items = None
        if not isinstance(items, list):
            raise ScheduleError("日程文件必须包含 items 数组。")
        return [item for item in items if isinstance(item, Mapping)]

    def _write(self, schedules: list[Schedule]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": SCHEMA_VERSION,
            "items": [schedule.to_dict() for schedule in schedules],
        }
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f"{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
                json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_name, self.path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def list(self) -> list[Schedule]:
        with self._lock:
            return [
                Schedule.from_dict(item)
                for item in self._read_items(self.path)
            ]

    def get(self, schedule_id: str) -> Schedule:
        with self._lock:
            for schedule in self.list():
                if schedule.id == schedule_id:
                    return schedule
        raise ScheduleNotFound(f"日程 {schedule_id} 不存在。")

    def create(self, payload: Mapping[str, Any]) -> Schedule:
        with self._lock:
            schedules = self.list()
            schedule = Schedule.from_dict(payload, allow_missing_id=True)
            if any(item.id == schedule.id for item in schedules):
                raise ScheduleError(f"日程 {schedule.id} 已存在。")
            schedules.append(schedule)
            self._write(schedules)
            return schedule

    def update(self, schedule_id: str, updates: Mapping[str, Any]) -> Schedule:
        with self._lock:
            schedules = self.list()
            for index, schedule in enumerate(schedules):
                if schedule.id != schedule_id:
                    continue
                updated = schedule.with_updates(updates)
                schedules[index] = updated
                self._write(schedules)
                return updated
        raise ScheduleNotFound(f"日程 {schedule_id} 不存在。")

    def delete(self, schedule_id: str) -> None:
        with self._lock:
            schedules = self.list()
            remaining = [item for item in schedules if item.id != schedule_id]
            if len(remaining) == len(schedules):
                raise ScheduleNotFound(f"日程 {schedule_id} 不存在。")
            self._write(remaining)

    def summary(self) -> dict[str, object]:
        schedules = self.list()
        counts = {schedule_type: 0 for schedule_type in SCHEDULE_TYPES}
        for schedule in schedules:
            counts[schedule.type] += 1
        return {
            "path": str(self.path),
            "total": len(schedules),
            "types": counts,
        }
