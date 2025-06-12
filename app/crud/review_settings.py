"""
复习设置的数据库操作模块
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.review_settings import ReviewSetting


async def get_review_settings(db: AsyncSession) -> list[ReviewSetting]:
    """
    获取所有复习间隔设置
    
    参数:
        db: 数据库会话
        
    返回:
        list[ReviewSetting]: 复习设置列表
    """
    result = await db.execute(
        select(ReviewSetting)
        .filter(ReviewSetting.is_active == True)
        .order_by(ReviewSetting.review_count)
    )
    return result.scalars().all() 