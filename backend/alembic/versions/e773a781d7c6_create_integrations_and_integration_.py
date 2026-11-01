"""Create integrations and integration_sync_logs tables

Revision ID: e773a781d7c6
Revises: 8e59589d4cd4
Create Date: 2026-05-12 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e773a781d7c6'
down_revision = '8e59589d4cd4'
branch_labels = None
depends_on = None


def upgrade():
    # Create integrations table
    op.create_table(
        'integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('encrypted_credentials', sa.Text(), nullable=False),
        sa.Column('encryption_salt', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('connection_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('test_error_message', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=True),
        sa.Column('total_candidates_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_integrations_org_id', 'integrations', ['org_id'], unique=False)
    op.create_index('idx_integrations_platform', 'integrations', ['platform'], unique=False)

    # Create integration_sync_logs table
    op.create_table(
        'integration_sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', sa.String(length=20), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sync_started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('sync_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=True),
        sa.Column('total_candidates_fetched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_deduplicated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['job_postings.job_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sync_logs_integration_id', 'integration_sync_logs', ['integration_id'], unique=False)
    op.create_index('idx_sync_logs_job_id', 'integration_sync_logs', ['job_id'], unique=False)
    op.create_index('idx_sync_logs_org_id', 'integration_sync_logs', ['org_id'], unique=False)
    op.create_index('idx_sync_logs_status', 'integration_sync_logs', ['sync_status'], unique=False)


def downgrade():
    op.drop_index('idx_sync_logs_status', table_name='integration_sync_logs')
    op.drop_index('idx_sync_logs_org_id', table_name='integration_sync_logs')
    op.drop_index('idx_sync_logs_job_id', table_name='integration_sync_logs')
    op.drop_index('idx_sync_logs_integration_id', table_name='integration_sync_logs')
    op.drop_table('integration_sync_logs')
    op.drop_index('idx_integrations_platform', table_name='integrations')
    op.drop_index('idx_integrations_org_id', table_name='integrations')
    op.drop_table('integrations')
