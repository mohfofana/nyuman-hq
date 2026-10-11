"""objectifs de pôle et rapports de la semaine

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import core.database

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("objectif", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pole", sa.String(length=20), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("current_manual", sa.Float(), nullable=True))
        batch_op.create_index(batch_op.f("ix_objectif_pole"), ["pole"], unique=False)

    op.create_table(
        "rapport",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("week", sa.String(length=10), nullable=False),
        sa.Column("pole", sa.String(length=20), nullable=False),
        sa.Column("fait", sa.Text(), nullable=False),
        sa.Column("en_cours", sa.Text(), nullable=False),
        sa.Column("bloque", sa.Text(), nullable=False),
        sa.Column("propositions", sa.Text(), nullable=False),
        sa.Column("created_at", core.database.UtcDateTime(), nullable=False),
        sa.Column("updated_at", core.database.UtcDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["membre.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("author_id", "week", name="uq_rapport_auteur_semaine"),
    )
    with op.batch_alter_table("rapport", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_rapport_author_id"), ["author_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_rapport_week"), ["week"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("rapport", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_rapport_week"))
        batch_op.drop_index(batch_op.f("ix_rapport_author_id"))
    op.drop_table("rapport")
    with op.batch_alter_table("objectif", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_objectif_pole"))
        batch_op.drop_column("current_manual")
        batch_op.drop_column("pole")
