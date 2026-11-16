"""create_submissions_chunks

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-16 23:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 6. Submissions table
    op.create_table(
        'submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_label', sa.String(length=255), nullable=False),
        sa.Column('student_id', sa.String(length=100), nullable=True),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('extraction_status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evaluation_id', 'file_hash', name='uq_evaluation_file_hash')
    )
    op.create_index('idx_submissions_evaluation', 'submissions', ['evaluation_id'], unique=False)
    op.create_index('idx_submissions_hash', 'submissions', ['file_hash'], unique=False)
    op.create_index('idx_submissions_status', 'submissions', ['extraction_status'], unique=False)

    # 7. Submission Chunks table
    op.create_table(
        'submission_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('paragraph', sa.Integer(), nullable=False),
        sa.Column('offset', sa.Integer(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('normalized_text', sa.Text(), nullable=False),
        sa.Column('embedding_ref', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_submission_chunks_sub_page', 'submission_chunks', ['submission_id', 'page', 'paragraph'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_submission_chunks_sub_page', table_name='submission_chunks')
    op.drop_table('submission_chunks')
    op.drop_index('idx_submissions_status', table_name='submissions')
    op.drop_index('idx_submissions_hash', table_name='submissions')
    op.drop_index('idx_submissions_evaluation', table_name='submissions')
    op.drop_table('submissions')
