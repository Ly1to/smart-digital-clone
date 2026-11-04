"""创建 schedules 表

Revision ID: 0001
Revises:
Create Date: 2026-11-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(trim(title)) > 0",
            name="ck_schedules_title_not_blank",
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_schedules_end_after_start",
        ),
        sa.CheckConstraint(
            "category IN ('work', 'outing', 'private')",
            name="ck_schedules_category_valid",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'cancelled')",
            name="ck_schedules_status_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_schedules_start_at", "schedules", ["start_at"], unique=False)
    op.create_index("ix_schedules_end_at", "schedules", ["end_at"], unique=False)
    op.create_index("ix_schedules_category", "schedules", ["category"], unique=False)
    op.create_index("ix_schedules_status", "schedules", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_schedules_status", table_name="schedules")
    op.drop_index("ix_schedules_category", table_name="schedules")
    op.drop_index("ix_schedules_end_at", table_name="schedules")
    op.drop_index("ix_schedules_start_at", table_name="schedules")
    op.drop_table("schedules")
