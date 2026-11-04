from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base
from app.models.enums import ScheduleCategory, ScheduleStatus


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_schedules_title_not_blank"),
        CheckConstraint("end_at > start_at", name="ck_schedules_end_after_start"),
        CheckConstraint(
            "category IN ('work', 'outing', 'private')",
            name="ck_schedules_category_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'cancelled')",
            name="ck_schedules_status_valid",
        ),
        Index("ix_schedules_start_at", "start_at"),
        Index("ix_schedules_end_at", "end_at"),
        Index("ix_schedules_category", "category"),
        Index("ix_schedules_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[ScheduleCategory] = mapped_column(
        SAEnum(
            ScheduleCategory,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[ScheduleStatus] = mapped_column(
        SAEnum(
            ScheduleStatus,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=ScheduleStatus.pending,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
