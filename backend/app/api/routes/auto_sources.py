from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.schemas.staging import GithubStatusResponse, GithubSyncResponse
from app.services import gitee_service, github_service
from app.services.exceptions import GithubConfigurationError

router = APIRouter(
    prefix="/auto-sources/github",
    tags=["auto-sources"],
    dependencies=[Depends(get_current_user)],
)

gitee_router = APIRouter(
    prefix="/auto-sources/gitee",
    tags=["auto-sources"],
    dependencies=[Depends(get_current_user)],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/status", response_model=GithubStatusResponse)
def github_status() -> GithubStatusResponse:
    return GithubStatusResponse(
        configured=bool(settings.github_username or settings.github_token),
        username=settings.github_username,
        lookback_days=settings.github_lookback_days,
        token_configured=bool(settings.github_token),
    )


@router.post("/sync", response_model=GithubSyncResponse)
def sync_github(db: DbSession) -> GithubSyncResponse:
    if not settings.github_username and not settings.github_token:
        raise GithubConfigurationError()

    result = github_service.sync_github(
        db,
        username=settings.github_username,
        token=settings.github_token,
        lookback_days=settings.github_lookback_days,
        api_url=settings.github_api_url,
        duration_minutes=settings.auto_schedule_duration_minutes,
        day_start_hour=settings.auto_schedule_day_start_hour,
        day_end_hour=settings.auto_schedule_day_end_hour,
    )
    return GithubSyncResponse(
        configured=True,
        scanned_events=result.scanned_events,
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        no_slot=result.no_slot,
        message=result.message,
    )


@gitee_router.get("/status", response_model=GithubStatusResponse)
def gitee_status() -> GithubStatusResponse:
    return GithubStatusResponse(
        configured=bool(settings.gitee_username),
        username=settings.gitee_username,
        lookback_days=settings.gitee_lookback_days,
        token_configured=bool(settings.gitee_access_token),
    )


@gitee_router.post("/sync", response_model=GithubSyncResponse)
def sync_gitee(db: DbSession) -> GithubSyncResponse:
    if not settings.gitee_username:
        raise GithubConfigurationError("未配置 GITEE_USERNAME，无法同步 Gitee 仓库更新")

    result = gitee_service.sync_gitee(
        db,
        username=settings.gitee_username,
        access_token=settings.gitee_access_token,
        lookback_days=settings.gitee_lookback_days,
        api_url=settings.gitee_api_url,
        duration_minutes=settings.auto_schedule_duration_minutes,
        day_start_hour=settings.auto_schedule_day_start_hour,
        day_end_hour=settings.auto_schedule_day_end_hour,
    )
    return GithubSyncResponse(
        configured=True,
        scanned_events=result.scanned_events,
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        no_slot=result.no_slot,
        message=result.message,
    )
