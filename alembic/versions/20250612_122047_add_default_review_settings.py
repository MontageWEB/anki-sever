"""Add default review settings

Revision ID: 20250612_122047
Revises: 9e956878800c
Create Date: 2024-05-12 12:20:47.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision: str = "20250612_122047"
down_revision: Union[str, None] = "9e956878800c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 插入默认的复习间隔设置
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    op.execute(
        f"""
        INSERT INTO review_settings 
        (review_count, interval_days, description, is_active, created_at, updated_at)
        VALUES 
        (1, 1, '第1次复习：1天后复习', true, '{now}', '{now}'),
        (2, 1, '第2次复习：1天后复习', true, '{now}', '{now}'),
        (3, 1, '第3次复习：1天后复习', true, '{now}', '{now}'),
        (4, 2, '第4次复习：2天后复习', true, '{now}', '{now}'),
        (5, 3, '第5次复习：3天后复习', true, '{now}', '{now}'),
        (6, 5, '第6次复习：5天后复习', true, '{now}', '{now}'),
        (7, 7, '第7次复习：7天后复习', true, '{now}', '{now}'),
        (8, 7, '第8次复习：7天后复习', true, '{now}', '{now}'),
        (9, 14, '第9次复习：14天后复习', true, '{now}', '{now}'),
        (10, 14, '第10次复习：14天后复习', true, '{now}', '{now}'),
        (11, 30, '第11次复习：30天后复习', true, '{now}', '{now}'),
        (12, 30, '第12次复习：30天后复习', true, '{now}', '{now}'),
        (13, 60, '第13次及以后：60天后复习', true, '{now}', '{now}')
        """
    )


def downgrade() -> None:
    # 删除所有复习间隔设置
    op.execute("DELETE FROM review_settings") 