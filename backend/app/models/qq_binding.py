from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base


class QqBinding(Base):
    """QQ（OneBot）账号与站内账号的绑定关系。"""

    __tablename__ = "qq_bindings"
    __table_args__ = (
        UniqueConstraint(
            "platform",
            "external_id",
            name="uq_qq_bindings_platform_external",
        ),
        Index("ix_qq_bindings_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, default="onebot")
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
