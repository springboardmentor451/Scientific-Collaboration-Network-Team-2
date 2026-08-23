"""add publication and publication_authors tables

Revision ID: eed291baa419
Revises: 6195da39eb66
Create Date: 2026-08-15 21:18:11.160410

NOTE: Originally an empty stub - see note in 6195da39eb66. Filled in so a
fresh install actually creates these tables. Has no effect on your existing
database, which is already stamped past this revision.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eed291baa419'
down_revision: Union[str, Sequence[str], None] = '6195da39eb66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'publications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('abstract', sa.String(), nullable=True),
        sa.Column('doi', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_publications_id'), 'publications', ['id'], unique=False)

    op.create_table(
        'publication_authors',
        sa.Column('publication_id', sa.Integer(), nullable=False),
        sa.Column('researcher_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['publication_id'], ['publications.id']),
        sa.ForeignKeyConstraint(['researcher_id'], ['researchers.id']),
        sa.PrimaryKeyConstraint('publication_id', 'researcher_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('publication_authors')
    op.drop_index(op.f('ix_publications_id'), table_name='publications')
    op.drop_table('publications')
