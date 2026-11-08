from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.time import to_utc
from app.db.session import get_db
from app.models.enums import ScheduleCategory, ScheduleStatus
from app.schemas.schedule import ScheduleCreate, ScheduleRead, ScheduleUpdate
from app.services import schedule_service

router = APIRouter(
    prefix="/schedules",
    tags=["schedules"],
    dependencies=[Depends(get_current_user)],
)

DbSession = Annotated[Session, Depends(get_db)]


def _parse_enum_list(
    raw: str | None,
    enum_type: type[ScheduleCategory] | type[ScheduleStatus],
    label: str,
) -> list | None:
    if not raw:
        return None
    values = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            values.append(enum_type(part))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"不支持的{label}：{part}",
            ) from exc
    return values or None


@router.get("", response_model=list[ScheduleRead])
def list_schedules(
    db: DbSession,
    start: Annotated[datetime | None, Query(description="查询区间开始，ISO 8601")] = None,
    end: Annotated[datetime | None, Query(description="查询区间结束，ISO 8601，不包含")] = None,
    categories: Annotated[str | None, Query(description="逗号分隔，如 work,outing")] = None,
    statuses: Annotated[str | None, Query(description="逗号分隔，如 pending,completed")] = None,
    keyword: Annotated[str | None, Query(max_length=200, description="匹配标题或描述")] = None,
) -> list:
    start = to_utc(start) if start is not None else None
    end = to_utc(end) if end is not None else None
    if start is not None and end is not None and end <= start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="查询结束时间必须晚于开始时间",
        )

    return schedule_service.list_schedules(
        db,
        start=start,
        end=end,
        categories=_parse_enum_list(categories, ScheduleCategory, "日程分类"),
        statuses=_parse_enum_list(statuses, ScheduleStatus, "日程状态"),
        keyword=keyword,
    )


@router.get("/{schedule_id}", response_model=ScheduleRead)
def get_schedule(schedule_id: int, db: DbSession):
    return schedule_service.get_schedule(db, schedule_id)


@router.post("", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: ScheduleCreate, db: DbSession):
    return schedule_service.create_schedule(db, payload)


@router.patch("/{schedule_id}", response_model=ScheduleRead)
def update_schedule(schedule_id: int, payload: ScheduleUpdate, db: DbSession):
    return schedule_service.update_schedule(db, schedule_id, payload)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: DbSession) -> None:
    schedule_service.delete_schedule(db, schedule_id)
