"""add user institution_id and publication_reviews table

Revision ID: 9f1a2b6c7d3e
Revises: 32a5ee870ff7
Create Date: 2026-08-29 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9f1a2b6c7d3e'
down_revision: Union[str, None] = '32a5ee870ff7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users.institution_id: home institution for staff accounts
    #     (institution_admin / reviewer) that don't carry a Researcher profile ---
    op.add_column('users', sa.Column('institution_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_users_institution_id'), 'users', ['institution_id'], unique=False)
    op.create_foreign_key(
        'fk_users_institution_id_institutions',
        'users', 'institutions',
        ['institution_id'], ['id'],
        ondelete='SET NULL',
    )

    # --- publication_reviews: reviewer assignments + decisions ---
    # NOTE: matching the convention used by every other enum in this schema
    # (user_role, publication_status, ...): SQLAlchemy's Enum type binds the
    # Python member *name* (e.g. "PENDING"), not its lowercase `.value`, so
    # the Postgres enum's labels must be the uppercase member names too.
    # create_type=False because we create the enum type ourselves right
    # below (checkfirst=True) — letting create_table's own ENUM handling run
    # too would try to CREATE TYPE a second time in the same transaction and
    # fail with "already exists".
    review_status = postgresql.ENUM(
        'PENDING', 'APPROVED', 'CHANGES_REQUESTED', 'REJECTED',
        name='review_status',
        create_type=False,
    )
    review_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'publication_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('publication_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', review_status, nullable=False, server_default='PENDING'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['publication_id'], ['publications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index(op.f('ix_publication_reviews_publication_id'), 'publication_reviews', ['publication_id'])
    op.create_index(op.f('ix_publication_reviews_reviewer_id'), 'publication_reviews', ['reviewer_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_publication_reviews_reviewer_id'), table_name='publication_reviews')
    op.drop_index(op.f('ix_publication_reviews_publication_id'), table_name='publication_reviews')
    op.drop_table('publication_reviews')
    postgresql.ENUM(name='review_status').drop(op.get_bind(), checkfirst=True)

    op.drop_constraint('fk_users_institution_id_institutions', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_institution_id'), table_name='users')
    op.drop_column('users', 'institution_id')
