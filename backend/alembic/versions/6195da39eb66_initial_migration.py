"""initial migration

Revision ID: 6195da39eb66
Revises: 
Create Date: 2026-08-07 17:51:41.487051

NOTE: This migration originally shipped as an empty stub (upgrade/downgrade
both just `pass`), even though the app's actual scientific_network.db already
had these tables (created by some other means, e.g. Base.metadata.create_all()
being run directly). That meant a fresh checkout running `alembic upgrade head`
from empty would end up with NO tables at all. Filled in below so a clean
install actually works. Your existing database is already stamped past this
revision, so this change has no effect on it - it only matters for new/fresh
databases.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6195da39eb66'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'institutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_institutions_id'), 'institutions', ['id'], unique=False)

    op.create_table(
        'researchers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('designation', sa.String(), nullable=True),
        sa.Column('institution_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_researchers_id'), 'researchers', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_researchers_id'), table_name='researchers')
    op.drop_table('researchers')
    op.drop_index(op.f('ix_institutions_id'), table_name='institutions')
    op.drop_table('institutions')
