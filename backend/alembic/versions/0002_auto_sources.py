"""添加自动来源与日程暂存区

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("schedules") as batch:
        batch.add_column(
            sa.Column(
                "source",
                sa.String(length=40),
                nullable=False,
                server_default="manual",
            )
        )
        batch.add_column(sa.Column("source_ref", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("source_url", sa.String(length=500), nullable=True))
        batch.create_index("ix_schedules_source", ["source"], unique=False)

    op.create_table(
        "staged_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("source_meta", sa.JSON(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("all_day", sa.Boolean(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(trim(title)) > 0",
            name="ck_staged_title_not_blank",
        ),
        sa.CheckConstraint(
            "start_at IS NULL OR end_at IS NULL OR end_at > start_at",
            name="ck_staged_end_after_start",
        ),
        sa.CheckConstraint(
            "category IN ('work', 'outing', 'private')",
            name="ck_staged_category_valid",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_staged_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["schedule_id"],
            ["schedules.id"],
            name="fk_staged_schedule_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_ref", name="uq_staged_source_ref"),
    )
    op.create_index("ix_staged_status", "staged_schedules", ["status"], unique=False)
    op.create_index(
        "ix_staged_created_at",
        "staged_schedules",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_staged_created_at", table_name="staged_schedules")
    op.drop_index("ix_staged_status", table_name="staged_schedules")
    op.drop_table("staged_schedules")

    with op.batch_alter_table("schedules") as batch:
        batch.drop_index("ix_schedules_source")
        batch.drop_column("source_url")
        batch.drop_column("source_ref")
        batch.drop_column("source")
