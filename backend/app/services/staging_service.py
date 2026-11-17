from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import normalize_all_day, to_utc, utc_now
from app.models.enums import ScheduleCategory, ScheduleStatus, StagedStatus
from app.models.schedule import Schedule
from app.models.staging import StagedSchedule
from app.schemas.staging import StagedScheduleUpdate
from app.services.exceptions import (
    NoFreeSlotError,
    StagedScheduleNotFoundError,
    StagedScheduleStateError,
    StagedScheduleTimeError,
)
from app.services.scheduling import TimeInterval, find_free_slot
from app.services.sync_lock import synchronized


def local_now() -> datetime:
    return datetime.now().astimezone()


def _day_bounds(now: datetime, start_hour: int, end_hour: int) -> tuple[datetime, datetime]:
    local = now.astimezone()
    day_start = datetime.combine(local.date(), time(start_hour), tzinfo=local.tzinfo)
    if end_hour >= 24:
        day_end = datetime.combine(local.date() + timedelta(days=1), time(0), tzinfo=local.tzinfo)
    else:
        day_end = datetime.combine(local.date(), time(end_hour), tzinfo=local.tzinfo)
    return day_start.astimezone(UTC), day_end.astimezone(UTC)


def _busy_intervals(
    db: Session,
    *,
    user_id: int,
    day_start: datetime,
    day_end: datetime,
    exclude_staged_id: int | None = None,
) -> list[TimeInterval]:
    schedules = db.scalars(
        select(Schedule).where(
            Schedule.user_id == user_id,
            Schedule.start_at < day_end,
            Schedule.end_at > day_start,
            Schedule.status != ScheduleStatus.cancelled,
        )
    )
    intervals = [
        TimeInterval(to_utc(schedule.start_at), to_utc(schedule.end_at)) for schedule in schedules
    ]

    staged_query = select(StagedSchedule).where(
        StagedSchedule.user_id == user_id,
        StagedSchedule.status == StagedStatus.pending,
        StagedSchedule.start_at.is_not(None),
        StagedSchedule.end_at.is_not(None),
        StagedSchedule.start_at < day_end,
        StagedSchedule.end_at > day_start,
    )
    if exclude_staged_id is not None:
        staged_query = staged_query.where(StagedSchedule.id != exclude_staged_id)
    for staged in db.scalars(staged_query):
        intervals.append(TimeInterval(to_utc(staged.start_at), to_utc(staged.end_at)))

    return intervals


def _duration(staged: StagedSchedule, default_minutes: int) -> timedelta:
    if (
        not staged.all_day
        and staged.start_at is not None
        and staged.end_at is not None
        and staged.end_at > staged.start_at
    ):
        return to_utc(staged.end_at) - to_utc(staged.start_at)
    return timedelta(minutes=default_minutes)


def assign_slot(
    db: Session,
    staged: StagedSchedule,
    *,
    now: datetime | None = None,
    duration_minutes: int = 30,
    day_start_hour: int = 9,
    day_end_hour: int = 22,
) -> TimeInterval | None:
    """为暂存日程分配当天第一个空闲时段；没有空位时清空建议时间。"""
    if staged.user_id is None:
        raise ValueError("暂存日程缺少用户归属")
    current = now or local_now()
    day_start, day_end = _day_bounds(current, day_start_hour, day_end_hour)
    busy = _busy_intervals(
        db,
        user_id=staged.user_id,
        day_start=day_start,
        day_end=day_end,
        exclude_staged_id=staged.id,
    )
    slot = find_free_slot(
        busy,
        day_start=day_start,
        day_end=day_end,
        duration=timedelta(minutes=duration_minutes),
        not_before=current.astimezone(UTC),
    )
    staged.start_at = slot.start if slot else None
    staged.end_at = slot.end if slot else None
    return slot


def _proposed_slot_is_usable(
    db: Session,
    staged: StagedSchedule,
    *,
    now: datetime,
    day_start: datetime,
    day_end: datetime,
) -> TimeInterval | None:
    if staged.start_at is None or staged.end_at is None:
        return None
    start = to_utc(staged.start_at)
    end = to_utc(staged.end_at)
    if end <= start or start < day_start or end > day_end:
        return None
    if start < now.astimezone(UTC) - timedelta(minutes=5):
        return None
    if staged.user_id is None:
        return None
    busy = _busy_intervals(
        db,
        user_id=staged.user_id,
        day_start=day_start,
        day_end=day_end,
        exclude_staged_id=staged.id,
    )
    for interval in busy:
        if start < interval.end and end > interval.start:
            return None
    return TimeInterval(start, end)


def _all_day_interval(staged: StagedSchedule, now: datetime) -> TimeInterval:
    if staged.start_at is not None and staged.end_at is not None:
        start, end = normalize_all_day(staged.start_at, staged.end_at)
        return TimeInterval(start, end)
    anchor = datetime.combine(now.date(), time.min, tzinfo=UTC)
    return TimeInterval(anchor, datetime.combine(now.date(), time.max, tzinfo=UTC))


def list_staged(
    db: Session,
    *,
    user_id: int,
    status: StagedStatus | None = StagedStatus.pending,
) -> list[StagedSchedule]:
    stmt = select(StagedSchedule).where(StagedSchedule.user_id == user_id)
    if status is not None:
        stmt = stmt.where(StagedSchedule.status == status)
    stmt = stmt.order_by(
        StagedSchedule.start_at.is_(None),
        StagedSchedule.start_at.asc(),
        StagedSchedule.id.asc(),
    )
    return list(db.scalars(stmt))


def get_staged(db: Session, staged_id: int, user_id: int) -> StagedSchedule:
    staged = db.scalar(
        select(StagedSchedule).where(
            StagedSchedule.id == staged_id,
            StagedSchedule.user_id == user_id,
        )
    )
    if staged is None:
        raise StagedScheduleNotFoundError(staged_id)
    return staged


def _validate_staged_times(staged: StagedSchedule) -> None:
    if staged.start_at is None or staged.end_at is None:
        return
    start = to_utc(staged.start_at)
    end = to_utc(staged.end_at)
    if staged.all_day:
        start, end = normalize_all_day(start, end)
        staged.start_at, staged.end_at = start, end
    if end <= start:
        raise StagedScheduleTimeError("结束时间必须晚于开始时间")


def update_staged(
    db: Session,
    staged_id: int,
    payload: StagedScheduleUpdate,
    user_id: int,
) -> StagedSchedule:
    staged = get_staged(db, staged_id, user_id)
    if staged.status != StagedStatus.pending:
        raise StagedScheduleStateError("只有待确认的暂存日程可以修改")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(staged, field, value)
    _validate_staged_times(staged)
    db.commit()
    db.refresh(staged)
    return staged


def reject_staged(db: Session, staged_id: int, user_id: int) -> StagedSchedule:
    staged = get_staged(db, staged_id, user_id)
    if staged.status != StagedStatus.pending:
        raise StagedScheduleStateError("只有待确认的暂存日程可以忽略")
    staged.status = StagedStatus.rejected
    db.commit()
    db.refresh(staged)
    return staged


@synchronized
def approve_staged(
    db: Session,
    staged_id: int,
    *,
    user_id: int,
    now: datetime | None = None,
    duration_minutes: int = 30,
    day_start_hour: int = 9,
    day_end_hour: int = 22,
) -> tuple[StagedSchedule, Schedule]:
    staged = get_staged(db, staged_id, user_id)
    if staged.status != StagedStatus.pending:
        raise StagedScheduleStateError("这条暂存日程已经处理过了")

    current = now or local_now()
    if staged.all_day:
        interval = _all_day_interval(staged, current)
    else:
        day_start, day_end = _day_bounds(current, day_start_hour, day_end_hour)
        interval = _proposed_slot_is_usable(
            db,
            staged,
            now=current,
            day_start=day_start,
            day_end=day_end,
        )
        if interval is None:
            busy = _busy_intervals(
                db,
                user_id=user_id,
                day_start=day_start,
                day_end=day_end,
                exclude_staged_id=staged.id,
            )
            interval = find_free_slot(
                busy,
                day_start=day_start,
                day_end=day_end,
                duration=_duration(staged, duration_minutes),
                not_before=current.astimezone(UTC),
            )
        if interval is None:
            raise NoFreeSlotError()

    schedule = Schedule(
        user_id=staged.user_id,
        title=staged.title,
        category=staged.category,
        description=staged.description,
        start_at=interval.start,
        end_at=interval.end,
        all_day=staged.all_day,
        location=staged.location,
        status=ScheduleStatus.pending,
        source=staged.source,
        source_ref=staged.source_ref,
        source_url=staged.source_url,
    )
    db.add(schedule)
    db.flush()

    staged.status = StagedStatus.approved
    staged.schedule_id = schedule.id
    staged.approved_at = utc_now()
    db.commit()
    db.refresh(staged)
    db.refresh(schedule)
    return staged, schedule


@synchronized
def approve_all_staged(
    db: Session,
    *,
    user_id: int,
    now: datetime | None = None,
    duration_minutes: int = 30,
    day_start_hour: int = 9,
    day_end_hour: int = 22,
) -> tuple[list[Schedule], list[StagedSchedule]]:
    pending = list_staged(db, user_id=user_id)
    approved: list[Schedule] = []
    skipped: list[StagedSchedule] = []
    current = now or local_now()

    for staged in pending:
        try:
            _, schedule = approve_staged(
                db,
                staged.id,
                user_id=user_id,
                now=current,
                duration_minutes=duration_minutes,
                day_start_hour=day_start_hour,
                day_end_hour=day_end_hour,
            )
            approved.append(schedule)
        except NoFreeSlotError:
            db.rollback()
            skipped.append(get_staged(db, staged.id, user_id))
    return approved, skipped


def count_pending(db: Session, *, user_id: int) -> int:
    return len(list_staged(db, user_id=user_id))


def new_staged(
    *,
    user_id: int,
    source: str,
    source_ref: str,
    source_url: str | None,
    title: str,
    category: ScheduleCategory,
    description: str | None,
    all_day: bool,
    location: str | None,
    source_meta: dict | None,
) -> StagedSchedule:
    return StagedSchedule(
        user_id=user_id,
        source=source,
        source_ref=source_ref,
        source_url=source_url,
        title=title,
        category=category,
        description=description,
        all_day=all_day,
        location=location,
        source_meta=source_meta,
        status=StagedStatus.pending,
    )
