"""create review rules table

Revision ID: 20240315_000001
Revises: 
Create Date: 2024-03-15 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20240315_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建复习规则表
    op.create_table(
        'review_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('review_count', sa.Integer(), nullable=False),
        sa.Column('interval_days', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_review_rules_id'), 'review_rules', ['id'], unique=False)
    op.create_index(op.f('ix_review_rules_review_count'), 'review_rules', ['review_count'], unique=True)
    
    # 插入默认规则
    default_rules = [
        (1, 1), (2, 1), (3, 1), (4, 2), (5, 3),
        (6, 5), (7, 7), (8, 7), (9, 14), (10, 14),
        (11, 30), (12, 30), (13, 60), (14, 60), (15, 60),
        (16, 60), (17, 60), (18, 60), (19, 60), (20, 60)
    ]
    
    for review_count, interval_days in default_rules:
        op.execute(
            sa.text(
                "INSERT INTO review_rules (review_count, interval_days) VALUES (:review_count, :interval_days)"
            ).bindparams(review_count=review_count, interval_days=interval_days)
        )


def downgrade() -> None:
    op.drop_index(op.f('ix_review_rules_review_count'), table_name='review_rules')
    op.drop_index(op.f('ix_review_rules_id'), table_name='review_rules')
    op.drop_table('review_rules') 