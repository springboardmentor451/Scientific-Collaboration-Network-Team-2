"""add new modules: users, projects, conferences, citations, audit_logs;
extend publications with type/status/year/venue/file_path

Revision ID: af2a0541ff76
Revises: 47be8a585737
Create Date: 2026-08-19 09:35:43.200888

This is the first "real" new migration added on top of the existing chain.
It only creates the NEW tables introduced by the extra backend modules, and
extends the existing (previously empty) `publications` table with the extra
columns the Publication Management module needs. It deliberately does NOT
recreate institutions/researchers/publications/publication_authors, since
those already exist in the current database.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af2a0541ff76'
down_revision: Union[str, Sequence[str], None] = '47be8a585737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Extend publications (table exists, but is empty of new columns) ---
    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'publication_type',
                sa.Enum(
                    'JOURNAL_PAPER', 'CONFERENCE_PAPER', 'BOOK', 'PATENT',
                    'TECHNICAL_REPORT', 'OTHER', name='publicationtype',
                ),
                nullable=False,
                server_default='OTHER',
            )
        )
        batch_op.add_column(
            sa.Column(
                'status',
                sa.Enum('DRAFT', 'SUBMITTED', 'PUBLISHED', 'ARCHIVED', name='publicationstatus'),
                nullable=False,
                server_default='DRAFT',
            )
        )
        batch_op.add_column(sa.Column('year', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('venue', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('file_path', sa.String(), nullable=True))

    # --- Users / Auth ---
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column(
            'role',
            sa.Enum('RESEARCHER', 'INSTITUTION_ADMIN', 'REVIEWER', 'SYSTEM_ADMIN', name='userrole'),
            nullable=False,
        ),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('researcher_id', sa.Integer(), nullable=True),
        sa.Column('institution_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id']),
        sa.ForeignKeyConstraint(['researcher_id'], ['researchers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # --- Research projects / collaboration ---
    op.create_table(
        'research_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('PLANNED', 'ACTIVE', 'COMPLETED', 'ON_HOLD', name='projectstatus'),
            nullable=False,
        ),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('funding_agency', sa.String(), nullable=True),
        sa.Column('funding_amount', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_research_projects_id'), 'research_projects', ['id'], unique=False)

    op.create_table(
        'project_members',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('researcher_id', sa.Integer(), nullable=False),
        sa.Column('role_in_project', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id']),
        sa.ForeignKeyConstraint(['researcher_id'], ['researchers.id']),
        sa.PrimaryKeyConstraint('project_id', 'researcher_id'),
    )

    op.create_table(
        'project_institutions',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id']),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id']),
        sa.PrimaryKeyConstraint('project_id', 'institution_id'),
    )

    # --- Conferences ---
    op.create_table(
        'conferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_conferences_id'), 'conferences', ['id'], unique=False)

    op.create_table(
        'conference_participations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conference_id', sa.Integer(), nullable=False),
        sa.Column('researcher_id', sa.Integer(), nullable=False),
        sa.Column('publication_id', sa.Integer(), nullable=True),
        sa.Column(
            'role',
            sa.Enum('PRESENTER', 'ATTENDEE', 'ORGANIZER', 'REVIEWER', name='participationrole'),
            nullable=False,
        ),
        sa.Column('presentation_title', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['conference_id'], ['conferences.id']),
        sa.ForeignKeyConstraint(['publication_id'], ['publications.id']),
        sa.ForeignKeyConstraint(['researcher_id'], ['researchers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_conference_participations_id'), 'conference_participations', ['id'], unique=False
    )

    # --- Citations & references ---
    op.create_table(
        'citations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('citing_publication_id', sa.Integer(), nullable=False),
        sa.Column('cited_publication_id', sa.Integer(), nullable=True),
        sa.Column('external_reference', sa.String(), nullable=True),
        sa.Column('doi', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['cited_publication_id'], ['publications.id']),
        sa.ForeignKeyConstraint(['citing_publication_id'], ['publications.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_citations_id'), 'citations', ['id'], unique=False)

    # --- Audit logs ---
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_role', sa.String(), nullable=True),
        sa.Column('client_ip', sa.String(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_path'), 'audit_logs', ['path'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_path'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_citations_id'), table_name='citations')
    op.drop_table('citations')

    op.drop_index(op.f('ix_conference_participations_id'), table_name='conference_participations')
    op.drop_table('conference_participations')
    op.drop_index(op.f('ix_conferences_id'), table_name='conferences')
    op.drop_table('conferences')

    op.drop_table('project_institutions')
    op.drop_table('project_members')
    op.drop_index(op.f('ix_research_projects_id'), table_name='research_projects')
    op.drop_table('research_projects')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.drop_column('file_path')
        batch_op.drop_column('venue')
        batch_op.drop_column('year')
        batch_op.drop_column('status')
        batch_op.drop_column('publication_type')
