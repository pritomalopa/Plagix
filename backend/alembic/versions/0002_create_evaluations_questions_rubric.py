"""create_evaluations_questions_rubric

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-16 23:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 3. Evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('max_marks', sa.Integer(), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='created', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_evaluations_tenant_owner', 'evaluations', ['tenant_id', 'owner_id'], unique=False)
    op.create_index('idx_evaluations_status', 'evaluations', ['status'], unique=False)

    # 4. Questions table
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('reference_answer', sa.Text(), nullable=True),
        sa.Column('expected_concepts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('citation_policy', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evaluation_id', 'order', name='uq_evaluation_question_order')
    )
    op.create_index('idx_questions_eval_order', 'questions', ['evaluation_id', 'order'], unique=False)

    # 5. Rubric criteria table
    op.create_table(
        'rubric_criteria',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('criterion', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_points', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('expected_evidence', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rubric_question_order', 'rubric_criteria', ['question_id', 'order'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_rubric_question_order', table_name='rubric_criteria')
    op.drop_table('rubric_criteria')
    op.drop_index('idx_questions_eval_order', table_name='questions')
    op.drop_table('questions')
    op.drop_index('idx_evaluations_status', table_name='evaluations')
    op.drop_index('idx_evaluations_tenant_owner', table_name='evaluations')
    op.drop_table('evaluations')
