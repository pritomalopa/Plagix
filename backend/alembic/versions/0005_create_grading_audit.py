"""create_grading_audit

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-16 23:49:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 11. Code Analysis Results table
    op.create_table(
        'code_analysis_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('comparison_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.Column('token_similarity', sa.Float(), nullable=True),
        sa.Column('ast_similarity', sa.Float(), nullable=True),
        sa.Column('matched_spans', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('parser_version', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('(submission_id IS NOT NULL) OR (comparison_id IS NOT NULL)', name='check_code_analysis_target'),
        sa.ForeignKeyConstraint(['comparison_id'], ['comparisons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_code_analysis_submission', 'code_analysis_results', ['submission_id'], unique=False)
    op.create_index('idx_code_analysis_comparison', 'code_analysis_results', ['comparison_id'], unique=False)

    # 12. Grading Results table
    op.create_table(
        'grading_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('criterion_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('suggested_total', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('teacher_final_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('suggested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id')
    )
    op.create_index('idx_grading_results_status', 'grading_results', ['status'], unique=False)

    # 13. Processing Jobs table
    op.create_table(
        'processing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='queued', nullable=False),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('progress', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_processing_jobs_status_time', 'processing_jobs', ['status', 'created_at'], unique=False)
    op.create_index('idx_processing_jobs_eval_type_status', 'processing_jobs', ['evaluation_id', 'job_type', 'status'], unique=False)

    # 14. Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_tenant_time', 'audit_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index('idx_audit_logs_actor_time', 'audit_logs', ['actor_id', 'created_at'], unique=False)
    op.create_index('idx_audit_logs_target', 'audit_logs', ['target_type', 'target_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_audit_logs_target', table_name='audit_logs')
    op.drop_index('idx_audit_logs_actor_time', table_name='audit_logs')
    op.drop_index('idx_audit_logs_tenant_time', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('idx_processing_jobs_eval_type_status', table_name='processing_jobs')
    op.drop_index('idx_processing_jobs_status_time', table_name='processing_jobs')
    op.drop_table('processing_jobs')
    op.drop_index('idx_grading_results_status', table_name='grading_results')
    op.drop_table('grading_results')
    op.drop_index('idx_code_analysis_comparison', table_name='code_analysis_results')
    op.drop_index('idx_code_analysis_submission', table_name='code_analysis_results')
    op.drop_table('code_analysis_results')
