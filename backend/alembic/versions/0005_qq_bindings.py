"""添加 QQ 账号绑定

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "qq_bindings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "platform",
            "external_id",
            name="uq_qq_bindings_platform_external",
        ),
    )
    op.create_index("ix_qq_bindings_user_id", "qq_bindings", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_qq_bindings_user_id", table_name="qq_bindings")
    op.drop_table("qq_bindings")
