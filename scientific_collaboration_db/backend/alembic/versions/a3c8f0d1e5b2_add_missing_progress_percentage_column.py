"""add missing progress_percentage column to projects

Revision ID: a3c8f0d1e5b2
Revises: 9f1a2b6c7d3e
Create Date: 2026-08-30 05:00:00.000000

The Project model has declared `progress_percentage` for a while, but no
migration ever actually created the column — GET /projects has been 500ing
with `UndefinedColumn: projects.progress_percentage does not exist` on any
database that was migrated step-by-step rather than built fresh from the
current models. This closes that gap.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c8f0d1e5b2'
down_revision: Union[str, None] = '9f1a2b6c7d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('progress_percentage', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'progress_percentage')
