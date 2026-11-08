from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.core.time import serialize_utc, to_utc
from app.models.enums import ScheduleCategory, ScheduleStatus

Title = Annotated[str, Field(max_length=200)]
Description = Annotated[str | None, Field(max_length=5000)]
Location = Annotated[str | None, Field(max_length=200)]


class ScheduleCreate(BaseModel):
    title: Title
    category: ScheduleCategory
    description: Description = None
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    location: Location = None
    status: ScheduleStatus = ScheduleStatus.pending

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("标题不能为空")
        return value

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_datetime(cls, value: datetime) -> datetime:
        return to_utc(value)


class ScheduleUpdate(BaseModel):
    title: Title | None = None
    category: ScheduleCategory | None = None
    description: Description = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    location: Location | None = None
    status: ScheduleStatus | None = None

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


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: ScheduleCategory
    description: str | None
    start_at: datetime
    end_at: datetime
    all_day: bool
    location: str | None
    status: ScheduleStatus
    source: str = "manual"
    source_ref: str | None = None
    source_url: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("start_at", "end_at", "created_at", "updated_at")
    @classmethod
    def normalize_datetime(cls, value: datetime) -> datetime:
        return to_utc(value)

    @field_serializer("start_at", "end_at", "created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        return serialize_utc(value) or ""


class HealthResponse(BaseModel):
    status: str
    database: str
