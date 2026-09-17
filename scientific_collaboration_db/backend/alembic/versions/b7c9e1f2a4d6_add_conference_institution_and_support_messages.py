"""add conferences.institution_id and support_messages table

Revision ID: b7c9e1f2a4d6
Revises: a3c8f0d1e5b2
Create Date: 2026-09-02 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7c9e1f2a4d6'
down_revision: Union[str, None] = 'a3c8f0d1e5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- conferences.institution_id: which institution owns the conference,
    #     so an Institution Admin can only edit their own institution's
    #     conferences (NULL = platform-wide, System-Admin-created) ---
    op.add_column('conferences', sa.Column('institution_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_conferences_institution_id'), 'conferences', ['institution_id'], unique=False)
    op.create_foreign_key(
        'fk_conferences_institution_id_institutions',
        'conferences', 'institutions',
        ['institution_id'], ['id'],
        ondelete='SET NULL',
    )

    # --- support_messages: direct chat between Researcher/Reviewer/
    #     Institution Admin accounts and the System Admin team ---
    op.create_table(
        'support_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('thread_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_from_admin', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['thread_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_support_messages_thread_user_id'), 'support_messages', ['thread_user_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_support_messages_thread_user_id'), table_name='support_messages')
    op.drop_table('support_messages')

    op.drop_constraint('fk_conferences_institution_id_institutions', 'conferences', type_='foreignkey')
    op.drop_index(op.f('ix_conferences_institution_id'), table_name='conferences')
    op.drop_column('conferences', 'institution_id')
