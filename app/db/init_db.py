from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base
from app.db.session import engine
# 强制 import 所有模型，确保 Base 能发现所有表
from app.models import user, card, review_settings

async def init_db() -> None:
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 