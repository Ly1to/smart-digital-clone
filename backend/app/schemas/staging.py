from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.core.time import serialize_utc, to_utc
from app.models.enums import ScheduleCategory, StagedStatus
from app.schemas.schedule import Description, Location, ScheduleRead, Title


class StagedScheduleUpdate(BaseModel):
    title: Title | None = None
    category: ScheduleCategory | None = None
    description: Description = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    location: Location | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("标题不能为空")
        return value

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else to_utc(value)


class StagedScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_ref: str
    source_url: str | None
    source_meta: dict[str, Any] | None
    title: str
    category: ScheduleCategory
    description: str | None
    start_at: datetime | None
    end_at: datetime | None
    all_day: bool
    location: str | None
    status: StagedStatus
    schedule_id: int | None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None

    @field_validator("start_at", "end_at", "created_at", "updated_at", "approved_at")
    @classmethod
    def normalize_datetime(cls, value: datetime | None) -> datetime | None:
        return None if value is None else to_utc(value)

    @field_serializer("start_at", "end_at", "created_at", "updated_at", "approved_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        return serialize_utc(value)


class StagedApproveResult(BaseModel):
    staged: StagedScheduleRead
    schedule: ScheduleRead


class StagedApproveAllResult(BaseModel):
    approved: list[ScheduleRead]
    skipped: list[StagedScheduleRead]


class GithubStatusResponse(BaseModel):
    configured: bool
    username: str
    lookback_days: int
    token_configured: bool


class GithubSyncResponse(BaseModel):
    configured: bool
    scanned_events: int
    created: int
    updated: int
    skipped: int
    no_slot: int
    message: str
