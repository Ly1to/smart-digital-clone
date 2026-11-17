"""为日程和暂存区增加用户归属

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("schedules") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_schedules_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_index("ix_schedules_user_id", ["user_id"], unique=False)

    with op.batch_alter_table("staged_schedules") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.drop_constraint("uq_staged_source_ref", type_="unique")
        batch.create_unique_constraint(
            "uq_staged_user_source_ref",
            ["user_id", "source", "source_ref"],
        )
        batch.create_foreign_key(
            "fk_staged_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_index("ix_staged_user_id", ["user_id"], unique=False)

    # 旧数据属于系统里的第一个账号；没有账号时保持为空，
    # 由首次创建账号的逻辑认领。
    op.execute(
        "UPDATE schedules SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1) "
        "WHERE user_id IS NULL"
    )
    op.execute(
        "UPDATE staged_schedules SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1) "
        "WHERE user_id IS NULL"
    )


def downgrade() -> None:
    with op.batch_alter_table("staged_schedules") as batch:
        batch.drop_index("ix_staged_user_id")
        batch.drop_constraint("fk_staged_user_id", type_="foreignkey")
        batch.drop_constraint("uq_staged_user_source_ref", type_="unique")
        batch.create_unique_constraint(
            "uq_staged_source_ref",
            ["source", "source_ref"],
        )
        batch.drop_column("user_id")

    with op.batch_alter_table("schedules") as batch:
        batch.drop_index("ix_schedules_user_id")
        batch.drop_constraint("fk_schedules_user_id", type_="foreignkey")
        batch.drop_column("user_id")
