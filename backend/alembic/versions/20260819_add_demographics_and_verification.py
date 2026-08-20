"""add demographics and verification fields

Revision ID: 20260819_add_demographics
Revises: 
Create Date: 2026-08-19 18:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260819_add_demographics'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # User additions
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('verification_token', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('verification_sent_at', sa.DateTime(), nullable=True))

    # Researcher additions
    with op.batch_alter_table('researcher', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gender', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('gender_other', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('nationality', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('country', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('city', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('mobile_number', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('designation', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('highest_qualification', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('year_highest_qualification', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('google_scholar_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('researchgate_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('scopus_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('wos_id', sa.String(length=100), nullable=True))

    # Notification additions
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'))

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('verification_sent_at')
        batch_op.drop_column('verification_token')

    with op.batch_alter_table('researcher', schema=None) as batch_op:
        batch_op.drop_column('wos_id')
        batch_op.drop_column('scopus_id')
        batch_op.drop_column('researchgate_url')
        batch_op.drop_column('google_scholar_url')
        batch_op.drop_column('year_highest_qualification')
        batch_op.drop_column('highest_qualification')
        batch_op.drop_column('designation')
        batch_op.drop_column('mobile_number')
        batch_op.drop_column('city')
        batch_op.drop_column('country')
        batch_op.drop_column('nationality')
        batch_op.drop_column('gender_other')
        batch_op.drop_column('gender')

    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.drop_column('is_read')
