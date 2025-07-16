---
description: "数据库开发规范 - 模型定义、迁移管理、时区处理"
globs: ["app/models/**/*.py", "app/crud/**/*.py", "alembic/**/*.py"]
alwaysApply: true
---

# 数据库开发规范

## 模型定义规范

### 基础模型
```python
from app.db.base_class import Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

### 时间字段规范
- 所有时间字段使用 `DateTime` 类型
- 默认值使用 `lambda: datetime.now(timezone.utc)`
- 不使用已弃用的 `datetime.utcnow()`

### 索引规范
```python
# 唯一索引
__table_args__ = (
    Index('idx_user_openid', 'openid', unique=True),
)

# 普通索引
__table_args__ = (
    Index('idx_card_user_id', 'user_id'),
    Index('idx_card_next_review', 'next_review_at'),
)
```

## 迁移管理规范

### Alembic 使用
1. 生成迁移文件：`alembic revision --autogenerate -m "描述"`
2. 执行迁移：`alembic upgrade head`
3. 回滚迁移：`alembic downgrade -1`

### 迁移前检查
```bash
# 1. 检查数据库连接
mysql -u user -p database_name

# 2. 检查迁移历史
alembic history

# 3. 检查当前版本
alembic current

# 4. 验证迁移文件
alembic check
```

### 迁移文件规范
```python
"""添加用户昵称和头像字段

Revision ID: 20250621_094141
Revises: 20250618_121216
Create Date: 2025-06-21 09:41:41.123456

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 升级操作
    op.add_column('users', sa.Column('nickname', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('avatar', sa.Text(), nullable=True))

def downgrade():
    # 回滚操作
    op.drop_column('users', 'avatar')
    op.drop_column('users', 'nickname')
```

## 时区处理规范

### 问题描述
MySQL DATETIME 字段不存储时区信息，SQLAlchemy 读取后可能变成 naive datetime，与 aware datetime 比较时出错。

### 解决方案
```python
def fix_timezone_fields(obj):
    """修正对象时间字段的时区信息"""
    time_fields = ['created_at', 'updated_at', 'first_review_at', 'next_review_at']
    
    for field in time_fields:
        if hasattr(obj, field):
            value = getattr(obj, field)
            if value and value.tzinfo is None:
                setattr(obj, field, value.replace(tzinfo=timezone.utc))
```

### 关键方法修正
以下方法必须包含时区修正逻辑：
```python
async def get_card(db: AsyncSession, card_id: int, user_id: int):
    card = await db.get(Card, card_id)
    if card:
        fix_timezone_fields(card)  # 修正时区
    return card

async def update_review_progress(db: AsyncSession, card: Card, remembered: bool):
    fix_timezone_fields(card)  # 修正时区
    # 更新逻辑...
```

## CRUD 操作规范

### 异步操作
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_cards(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    query = select(Card).filter(Card.user_id == user_id).offset(skip).limit(limit)
    result = await db.execute(query)
    cards = result.scalars().all()
    
    # 修正时区
    for card in cards:
        fix_timezone_fields(card)
    
    return cards
```

### 错误处理
```python
async def create_card(db: AsyncSession, card_data: dict, user_id: int):
    try:
        card = Card(**card_data, user_id=user_id)
        db.add(card)
        await db.commit()
        await db.refresh(card)
        return card
    except Exception as e:
        await db.rollback()
        logger.error(f"创建卡片失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建卡片失败")
```

## MySQL 最佳实践

### 字符集和排序规则
```sql
-- 创建数据库时指定
CREATE DATABASE anki_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### 索引优化
```sql
-- 避免部分索引（MySQL 8.0 不支持）
-- 错误示例
CREATE UNIQUE INDEX idx_user_openid ON users(openid) WHERE is_active = 1;

-- 正确示例
CREATE UNIQUE INDEX idx_user_openid_active ON users(openid, is_active);
```

### 连接池配置
```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)
```

## 性能优化

### 查询优化
```python
# 使用 select 而不是 query
from sqlalchemy import select

# 正确
query = select(Card).filter(Card.user_id == user_id)

# 错误
query = db.query(Card).filter(Card.user_id == user_id)
```

### 批量操作
```python
# 批量插入
cards = [Card(title=f"卡片{i}", content=f"内容{i}") for i in range(100)]
db.add_all(cards)
await db.commit()
```

### 延迟加载
```python
# 使用 selectinload 预加载关联数据
from sqlalchemy.orm import selectinload

query = select(Card).options(selectinload(Card.user))
```

## 测试规范

### 测试数据库
```python
# conftest.py
@pytest.fixture
async def db():
    # 使用 SQLite 内存数据库进行测试
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()
```

### 数据清理
```python
@pytest.fixture(autouse=True)
async def cleanup_db(db):
    yield
    # 测试后清理数据
    await db.rollback()
``` 