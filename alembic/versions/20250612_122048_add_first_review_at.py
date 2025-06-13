"""add first_review_at to cards table

Revision ID: 20250612_122048
Revises: 20250612_122047
Create Date: 2024-03-21 12:20:48.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250612_122048'
down_revision: Union[str, None] = '20250612_122047'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 first_review_at 字段
    op.add_column('cards', sa.Column('first_review_at', sa.DateTime(timezone=True), nullable=True, comment='首次复习时间'))


def downgrade() -> None:
    # 删除 first_review_at 字段
    op.drop_column('cards', 'first_review_at') 