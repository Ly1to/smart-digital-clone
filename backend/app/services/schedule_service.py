from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.core.time import normalize_all_day, to_utc
from app.models.enums import ScheduleCategory, ScheduleStatus
from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.exceptions import ScheduleNotFoundError, ScheduleTimeRangeError


def _validate_and_normalize(
    start_at: datetime,
    end_at: datetime,
    all_day: bool,
) -> tuple[datetime, datetime]:
    start_at = to_utc(start_at)
    end_at = to_utc(end_at)
    if all_day:
        start_at, end_at = normalize_all_day(start_at, end_at)
    if end_at <= start_at:
        raise ScheduleTimeRangeError()
    return start_at, end_at


def get_schedule(db: Session, schedule_id: int) -> Schedule:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise ScheduleNotFoundError(schedule_id)
    return schedule


def list_schedules(
    db: Session,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    categories: list[ScheduleCategory] | None = None,
    statuses: list[ScheduleStatus] | None = None,
    keyword: str | None = None,
) -> list[Schedule]:
    stmt: Select[tuple[Schedule]] = select(Schedule)

    # 区间查询使用半开区间：只要日程与 [start, end) 有交集就返回。
    if start is not None:
        stmt = stmt.where(Schedule.end_at >= start)
    if end is not None:
        stmt = stmt.where(Schedule.start_at < end)
    if categories:
        stmt = stmt.where(Schedule.category.in_(categories))
    if statuses:
        stmt = stmt.where(Schedule.status.in_(statuses))
    if keyword:
        pattern = keyword.strip()
        if pattern:
            stmt = stmt.where(
                or_(
                    Schedule.title.contains(pattern, autoescape=True),
                    Schedule.description.contains(pattern, autoescape=True),
                )
            )

    stmt = stmt.order_by(Schedule.start_at.asc(), Schedule.id.asc())
    return list(db.scalars(stmt))


def create_schedule(db: Session, payload: ScheduleCreate) -> Schedule:
    start_at, end_at = _validate_and_normalize(payload.start_at, payload.end_at, payload.all_day)
    schedule = Schedule(
        title=payload.title,
        category=payload.category,
        description=payload.description,
        start_at=start_at,
        end_at=end_at,
        all_day=payload.all_day,
        location=payload.location,
        status=payload.status,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(db: Session, schedule_id: int, payload: ScheduleUpdate) -> Schedule:
    schedule = get_schedule(db, schedule_id)
    changes = payload.model_dump(exclude_unset=True)

    start_at = changes.get("start_at", schedule.start_at)
    end_at = changes.get("end_at", schedule.end_at)
    all_day = changes.get("all_day", schedule.all_day)
    start_at, end_at = _validate_and_normalize(start_at, end_at, all_day)

    changes["start_at"] = start_at
    changes["end_at"] = end_at
    for field, value in changes.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, schedule_id: int) -> None:
    schedule = get_schedule(db, schedule_id)
    db.delete(schedule)
    db.commit()
