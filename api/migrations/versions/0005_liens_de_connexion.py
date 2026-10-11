"""liens de connexion envoyés par email

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import core.database

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lien_connexion",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("membre_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", core.database.UtcDateTime(), nullable=False),
        sa.Column("used_at", core.database.UtcDateTime(), nullable=True),
        sa.Column("created_at", core.database.UtcDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["membre_id"], ["membre.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    with op.batch_alter_table("lien_connexion", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_lien_connexion_membre_id"), ["membre_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("lien_connexion", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_lien_connexion_membre_id"))
    op.drop_table("lien_connexion")
