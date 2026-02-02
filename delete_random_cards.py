#!/usr/bin/env python3
"""
随机删除指定用户的卡片脚本

功能：随机删除用户ID为6的50个卡片
"""

import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.card import Card
from app.core.config import settings

async def delete_random_cards(user_id: int, count: int):
    """
    随机删除指定用户的卡片
    
    Args:
        user_id: 用户ID
        count: 要删除的卡片数量
    """
    # 创建异步数据库引擎
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,  # 设置为True可以看到SQL语句
    )
    
    # 创建异步会话工厂
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        try:
            # 查询用户的所有卡片
            stmt = select(Card).where(Card.user_id == user_id)
            result = await session.execute(stmt)
            cards = result.scalars().all()
            
            print(f"找到用户ID {user_id} 的卡片数量: {len(cards)}")
            
            if len(cards) < count:
                print(f"卡片数量不足 {count}，将删除所有 {len(cards)} 个卡片")
                cards_to_delete = cards
            else:
                # 随机选择指定数量的卡片
                cards_to_delete = random.sample(cards, count)
                print(f"随机选择了 {count} 个卡片进行删除")
            
            # 删除卡片
            deleted_count = 0
            for card in cards_to_delete:
                await session.delete(card)
                deleted_count += 1
                if deleted_count % 10 == 0:
                    print(f"已删除 {deleted_count} 个卡片...")
            
            # 提交事务
            await session.commit()
            print(f"\n删除完成！共删除了 {deleted_count} 个卡片")
            
        except Exception as e:
            await session.rollback()
            print(f"删除过程中出错: {e}")
        finally:
            await engine.dispose()

if __name__ == "__main__":
    import asyncio
    
    # 设置要删除的用户ID和卡片数量
    target_user_id = 6
    delete_count = 10
    
    print(f"开始删除用户ID {target_user_id} 的 {delete_count} 个随机卡片...")
    asyncio.run(delete_random_cards(target_user_id, delete_count))
    print("操作完成！")
