from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.config import settings
from app.db.session import get_db
from app.models.enums import StagedStatus
from app.schemas.staging import (
    StagedApproveAllResult,
    StagedApproveResult,
    StagedScheduleRead,
    StagedScheduleUpdate,
)
from app.services import staging_service

router = APIRouter(prefix="/staging", tags=["staging"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[StagedScheduleRead])
def list_staged(
    db: DbSession,
    current_user: CurrentUser,
    status: Annotated[StagedStatus, Query(description="暂存状态")] = StagedStatus.pending,
) -> list:
    return staging_service.list_staged(db, user_id=current_user.id, status=status)


@router.post("/approve-all", response_model=StagedApproveAllResult)
def approve_all_staged(db: DbSession, current_user: CurrentUser) -> StagedApproveAllResult:
    approved, skipped = staging_service.approve_all_staged(
        db,
        user_id=current_user.id,
        duration_minutes=settings.auto_schedule_duration_minutes,
        day_start_hour=settings.auto_schedule_day_start_hour,
        day_end_hour=settings.auto_schedule_day_end_hour,
    )
    return StagedApproveAllResult(approved=approved, skipped=skipped)


@router.patch("/{staged_id}", response_model=StagedScheduleRead)
def update_staged(
    staged_id: int,
    payload: StagedScheduleUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    return staging_service.update_staged(db, staged_id, payload, current_user.id)


@router.post("/{staged_id}/approve", response_model=StagedApproveResult)
def approve_staged(staged_id: int, db: DbSession, current_user: CurrentUser) -> StagedApproveResult:
    staged, schedule = staging_service.approve_staged(
        db,
        staged_id,
        user_id=current_user.id,
        duration_minutes=settings.auto_schedule_duration_minutes,
        day_start_hour=settings.auto_schedule_day_start_hour,
        day_end_hour=settings.auto_schedule_day_end_hour,
    )
    return StagedApproveResult(staged=staged, schedule=schedule)


@router.post("/{staged_id}/reject", response_model=StagedScheduleRead)
def reject_staged(staged_id: int, db: DbSession, current_user: CurrentUser):
    return staging_service.reject_staged(db, staged_id, current_user.id)
