from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base
from app.models.enums import ScheduleCategory, StagedStatus


class StagedSchedule(Base):
    """自动来源的待确认日程，类似 git 暂存区。"""

    __tablename__ = "staged_schedules"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_staged_title_not_blank"),
        CheckConstraint(
            "start_at IS NULL OR end_at IS NULL OR end_at > start_at",
            name="ck_staged_end_after_start",
        ),
        CheckConstraint(
            "category IN ('work', 'outing', 'private')",
            name="ck_staged_category_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_staged_status_valid",
        ),
        UniqueConstraint("user_id", "source", "source_ref", name="uq_staged_user_source_ref"),
        Index("ix_staged_user_id", "user_id"),
        Index("ix_staged_status", "status"),
        Index("ix_staged_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="github")
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

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
        default=ScheduleCategory.work,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    status: Mapped[StagedStatus] = mapped_column(
        SAEnum(
            StagedStatus,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        default=StagedStatus.pending,
    )
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
