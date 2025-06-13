"""
复习规则的数据库操作模块
实现了复习规则的增删改查（CRUD）操作
"""

from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review_rule import ReviewRule
from app.schemas.review_rule import ReviewRuleUpdate


async def get_review_rules(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100
) -> List[ReviewRule]:
    """
    获取复习规则列表
    
    参数：
        db: 数据库会话
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        
    返回：
        List[ReviewRule]: 复习规则列表
    """
    result = await db.execute(
        select(ReviewRule)
        .order_by(ReviewRule.review_count)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_review_rules(
    db: AsyncSession,
    *,
    rules_in: List[ReviewRuleUpdate]
) -> List[ReviewRule]:
    """
    批量更新复习规则
    
    参数：
        db: 数据库会话
        rules_in: 复习规则更新对象列表
        
    返回：
        List[ReviewRule]: 更新后的复习规则列表
    """
    updated_rules = []
    for rule_in in rules_in:
        # 查找对应的规则
        result = await db.execute(
            select(ReviewRule).filter(ReviewRule.review_count == rule_in.review_count)
        )
        rule = result.scalar_one_or_none()
        if rule:
            # 更新规则
            rule.interval_days = rule_in.interval_days
            updated_rules.append(rule)
    
    await db.commit()
    for rule in updated_rules:
        await db.refresh(rule)
    
    return updated_rules


async def reset_review_rules(db: AsyncSession) -> List[ReviewRule]:
    """
    重置复习规则为默认值
    
    参数：
        db: 数据库会话
        
    返回：
        List[ReviewRule]: 重置后的复习规则列表
    """
    # 删除所有现有规则
    await db.execute(delete(ReviewRule))
    
    # 插入默认规则
    default_rules = [
        (1, 1), (2, 1), (3, 1), (4, 2), (5, 3),
        (6, 5), (7, 7), (8, 7), (9, 14), (10, 14),
        (11, 30), (12, 30), (13, 60), (14, 60), (15, 60),
        (16, 60), (17, 60), (18, 60), (19, 60), (20, 60)
    ]
    
    rules = []
    for review_count, interval_days in default_rules:
        rule = ReviewRule(
            review_count=review_count,
            interval_days=interval_days
        )
        db.add(rule)
        rules.append(rule)
    
    await db.commit()
    for rule in rules:
        await db.refresh(rule)
    
    return rules 