"""create_relevance_comparisons

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-16 23:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 8. Relevance Results table
    op.create_table(
        'relevance_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model_version', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', 'question_id', name='uq_submission_question_relevance')
    )
    op.create_index('idx_relevance_category', 'relevance_results', ['category'], unique=False)

    # 9. Comparisons table (with canonical pair constraint & unique index)
    op.create_table(
        'comparisons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_a_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_b_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('exact_score', sa.Float(), nullable=True),
        sa.Column('lexical_score', sa.Float(), nullable=True),
        sa.Column('semantic_score', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('submission_a_id < submission_b_id', name='check_canonical_pair'),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_a_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_b_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evaluation_id', 'submission_a_id', 'submission_b_id', name='uq_evaluation_canonical_pair')
    )
    op.create_index('idx_comparisons_eval_status', 'comparisons', ['evaluation_id', 'status'], unique=False)

    # 10. Matched Passages table
    op.create_table(
        'matched_passages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('comparison_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text_a_page', sa.Integer(), nullable=True),
        sa.Column('text_a_offset', sa.Integer(), nullable=True),
        sa.Column('text_b_page', sa.Integer(), nullable=True),
        sa.Column('text_b_offset', sa.Integer(), nullable=True),
        sa.Column('text_a_excerpt', sa.Text(), nullable=False),
        sa.Column('text_b_excerpt', sa.Text(), nullable=False),
        sa.Column('match_type', sa.String(length=50), nullable=False),
        sa.Column('similarity', sa.Float(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['comparison_id'], ['comparisons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_matched_passages_comparison', 'matched_passages', ['comparison_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_matched_passages_comparison', table_name='matched_passages')
    op.drop_table('matched_passages')
    op.drop_index('idx_comparisons_eval_status', table_name='comparisons')
    op.drop_table('comparisons')
    op.drop_index('idx_relevance_category', table_name='relevance_results')
    op.drop_table('relevance_results')
