"""poles : l'organisation de Nyuman (CEO + 3 heads, un pôle chacun)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("membre", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pole", sa.String(length=20), nullable=False, server_default=""))
    with op.batch_alter_table("tache", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pole", sa.String(length=20), nullable=False, server_default=""))
        batch_op.create_index(batch_op.f("ix_tache_pole"), ["pole"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tache", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tache_pole"))
        batch_op.drop_column("pole")
    with op.batch_alter_table("membre", schema=None) as batch_op:
        batch_op.drop_column("pole")
