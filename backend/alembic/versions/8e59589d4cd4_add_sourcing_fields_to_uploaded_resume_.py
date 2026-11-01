"""add sourcing fields - external_candidate_id to uploaded_resumes

Revision ID: 8e59589d4cd4
Revises:
Create Date: 2026-05-12 15:05:45.275373

The is_sourced, source_type, source_channel, and source_platform columns
already exist in the database. This migration only adds the missing
external_candidate_id column to uploaded_resumes.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8e59589d4cd4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add external_candidate_id to uploaded_resumes if it doesn't exist
    # This column tracks the external platform's candidate ID (e.g., Naukri ID)
    op.add_column('uploaded_resumes', sa.Column('external_candidate_id', sa.String(length=255), nullable=True))


def downgrade():
    # Remove external_candidate_id from uploaded_resumes
    op.drop_column('uploaded_resumes', 'external_candidate_id')
