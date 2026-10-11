"""priorites, etapes, conseil et panel des pros

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import core.database


revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('decision',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('titre', sa.String(length=200), nullable=False),
    sa.Column('demande', sa.Text(), nullable=False),
    sa.Column('pole_concerne', sa.String(length=20), nullable=False),
    sa.Column('poles_en_charge', sa.String(length=100), nullable=False),
    sa.Column('objectif', sa.Text(), nullable=False),
    sa.Column('risques', sa.Text(), nullable=False),
    sa.Column('decision', sa.Text(), nullable=False),
    sa.Column('liens', sa.Text(), nullable=False),
    sa.Column('statut', sa.String(length=20), nullable=False),
    sa.Column('date_demande', sa.Date(), nullable=True),
    sa.Column('decided_at', core.database.UtcDateTime(), nullable=True),
    sa.Column('decided_by', sa.Integer(), nullable=True),
    sa.Column('bilan', sa.Text(), nullable=False),
    sa.Column('bilan_verdict', sa.String(length=20), nullable=False),
    sa.Column('bilan_at', core.database.UtcDateTime(), nullable=True),
    sa.Column('ref_externe', sa.String(length=80), nullable=True),
    sa.Column('archived', sa.Boolean(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('created_at', core.database.UtcDateTime(), nullable=False),
    sa.Column('updated_at', core.database.UtcDateTime(), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['membre.id'], ),
    sa.ForeignKeyConstraint(['decided_by'], ['membre.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ref_externe')
    )
    with op.batch_alter_table('decision', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_decision_statut'), ['statut'], unique=False)

    op.create_table('pro',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nom', sa.String(length=120), nullable=False),
    sa.Column('categorie', sa.String(length=20), nullable=False),
    sa.Column('enseigne', sa.String(length=120), nullable=False),
    sa.Column('audience', sa.String(length=40), nullable=False),
    sa.Column('telephone', sa.String(length=40), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('contrat', sa.String(length=20), nullable=False),
    sa.Column('acces_test', sa.String(length=20), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('suivi_par_id', sa.Integer(), nullable=True),
    sa.Column('numero', sa.Integer(), nullable=True),
    sa.Column('ref_externe', sa.String(length=80), nullable=True),
    sa.Column('archived', sa.Boolean(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', core.database.UtcDateTime(), nullable=False),
    sa.Column('updated_at', core.database.UtcDateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['membre.id'], ),
    sa.ForeignKeyConstraint(['suivi_par_id'], ['membre.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ref_externe')
    )
    with op.batch_alter_table('pro', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pro_categorie'), ['categorie'], unique=False)

    op.create_table('decision_vote',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('decision_id', sa.Integer(), nullable=False),
    sa.Column('membre_id', sa.Integer(), nullable=False),
    sa.Column('vote', sa.String(length=20), nullable=False),
    sa.Column('commentaire', sa.Text(), nullable=False),
    sa.Column('updated_at', core.database.UtcDateTime(), nullable=False),
    sa.ForeignKeyConstraint(['decision_id'], ['decision.id'], ),
    sa.ForeignKeyConstraint(['membre_id'], ['membre.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('decision_id', 'membre_id', name='uq_vote_decision_membre')
    )
    with op.batch_alter_table('decision_vote', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_decision_vote_decision_id'), ['decision_id'], unique=False)

    op.create_table('tache_etape',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tache_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('responsable_id', sa.Integer(), nullable=True),
    sa.Column('livrable', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('position', sa.Float(), nullable=False),
    sa.Column('ref_externe', sa.String(length=80), nullable=True),
    sa.Column('archived', sa.Boolean(), nullable=False),
    sa.Column('created_at', core.database.UtcDateTime(), nullable=False),
    sa.Column('updated_at', core.database.UtcDateTime(), nullable=False),
    sa.ForeignKeyConstraint(['responsable_id'], ['membre.id'], ),
    sa.ForeignKeyConstraint(['tache_id'], ['tache.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ref_externe')
    )
    with op.batch_alter_table('tache_etape', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tache_etape_tache_id'), ['tache_id'], unique=False)

    with op.batch_alter_table('tache', schema=None) as batch_op:
        batch_op.add_column(sa.Column('priority', sa.String(length=4), server_default='', nullable=False))
        batch_op.add_column(sa.Column('ref_externe', sa.String(length=80), nullable=True))
        batch_op.create_unique_constraint('uq_tache_ref_externe', ['ref_externe'])



def downgrade() -> None:
    with op.batch_alter_table('tache', schema=None) as batch_op:
        batch_op.drop_constraint('uq_tache_ref_externe', type_='unique')
        batch_op.drop_column('ref_externe')
        batch_op.drop_column('priority')

    with op.batch_alter_table('tache_etape', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tache_etape_tache_id'))

    op.drop_table('tache_etape')
    with op.batch_alter_table('decision_vote', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_decision_vote_decision_id'))

    op.drop_table('decision_vote')
    with op.batch_alter_table('pro', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pro_categorie'))

    op.drop_table('pro')
    with op.batch_alter_table('decision', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_decision_statut'))

    op.drop_table('decision')
