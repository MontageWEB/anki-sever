"""fix timezone fields

Revision ID: 1e2e2e2e2e2e
Revises: f3f061e2f9cc
Create Date: 2025-07-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = '1e2e2e2e2e2e'
down_revision = 'f3f061e2f9cc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 修改 cards 表的时间字段，支持时区
    op.execute("""
        ALTER TABLE cards 
        MODIFY COLUMN next_review_at DATETIME(6),
        MODIFY COLUMN created_at DATETIME(6),
        MODIFY COLUMN updated_at DATETIME(6)
    """)
    
    # 2. 修复现有数据，给无时区的时间补上 UTC 时区
    op.execute("""
        UPDATE cards 
        SET next_review_at = CONVERT_TZ(next_review_at, '+00:00', '+00:00'),
            created_at = CONVERT_TZ(created_at, '+00:00', '+00:00'),
            updated_at = CONVERT_TZ(updated_at, '+00:00', '+00:00')
        WHERE next_review_at IS NOT NULL 
           OR created_at IS NOT NULL 
           OR updated_at IS NOT NULL
    """)
    
    # 3. 修改 users 表的时间字段
    op.execute("""
        ALTER TABLE users 
        MODIFY COLUMN created_at DATETIME(6),
        MODIFY COLUMN updated_at DATETIME(6)
    """)
    
    # 4. 修复 users 表的数据
    op.execute("""
        UPDATE users 
        SET created_at = CONVERT_TZ(created_at, '+00:00', '+00:00'),
            updated_at = CONVERT_TZ(updated_at, '+00:00', '+00:00')
        WHERE created_at IS NOT NULL 
           OR updated_at IS NOT NULL
    """)


def downgrade():
    # 回滚：将时间字段改回 DATETIME
    op.execute("""
        ALTER TABLE cards 
        MODIFY COLUMN next_review_at DATETIME,
        MODIFY COLUMN created_at DATETIME,
        MODIFY COLUMN updated_at DATETIME
    """)
    
    op.execute("""
        ALTER TABLE users 
        MODIFY COLUMN created_at DATETIME,
        MODIFY COLUMN updated_at DATETIME
    """) 