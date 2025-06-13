"""
知识卡片的数据库操作模块
实现了卡片的增删改查（CRUD）操作和复习进度管理
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy import func

from app.models.card import Card
from app.schemas.card import CardCreate, CardUpdate
from app.core.config import settings
from app.core.review_strategy import ConfigurableReviewStrategy

# 创建可配置的复习策略实例
review_strategy = ConfigurableReviewStrategy(settings.REVIEW_STRATEGY_RULES)


async def create_card(db: AsyncSession, card: CardCreate) -> Card:
    """创建新卡片"""
    db_card = Card(
        question=card.question,
        answer=card.answer,
        review_count=0,
        next_review_at=datetime.now(timezone.utc)
    )
    db.add(db_card)
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def get_card(db: AsyncSession, card_id: int) -> Optional[Card]:
    """
    获取指定ID的卡片
    
    参数：
        db: 数据库会话
        card_id: 卡片ID
        
    返回：
        Card | None: 卡片对象，如果不存在则返回None
    """
    result = await db.execute(select(Card).filter(Card.id == card_id))
    return result.scalar_one_or_none()


async def get_cards(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None
) -> tuple[list[Card], int]:
    """
    获取卡片列表
    
    参数:
        db: 数据库会话
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        search: 搜索关键词（可选）
        
    返回:
        tuple[list[Card], int]: 卡片列表和总记录数
    """
    # 构建基础查询，添加按创建时间倒序排序
    query: Select = select(Card).order_by(Card.created_at.desc())
    count_query: Select = select(Card)

    # 如果有搜索关键词，添加搜索条件
    if search:
        search_filter = (
            Card.question.ilike(f"%{search}%") |
            Card.answer.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
        count_query = count_query.filter(search_filter)

    # 获取总数
    total_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
    total = total_result.scalar()

    # 获取分页数据
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all(), total


async def update_card(
    db: AsyncSession,
    *,
    db_card: Card,
    card_update: CardUpdate
) -> Card:
    """更新卡片"""
    for field, value in card_update.model_dump(exclude_unset=True).items():
        setattr(db_card, field, value)
    
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def delete_card(db: AsyncSession, *, db_card: Card) -> None:
    """删除卡片"""
    await db.delete(db_card)
    await db.commit()


async def get_cards_to_review(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20
) -> tuple[list[Card], int]:
    """
    获取今日待复习的卡片
    
    参数:
        db: 数据库会话
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        
    返回:
        tuple[list[Card], int]: 卡片列表和总记录数
    """
    # 获取当前 UTC 时间
    now = datetime.now(timezone.utc)
    
    # 获取今天的开始时间（UTC）
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    
    # 构建查询：获取今天及之前的待复习卡片
    query = (
        select(Card)
        .filter(Card.next_review_at <= now)  # 获取今天及之前的待复习卡片
        .order_by(Card.next_review_at)  # 按复习时间排序
    )
    
    # 获取总数
    count_query = select(func.count()).select_from(
        select(Card)
        .filter(Card.next_review_at <= now)
        .subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 获取分页数据
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all(), total


def get_cards_for_review(db: Session, limit: int = 100) -> List[Card]:
    """
    获取需要复习的卡片
    
    参数：
        db: 数据库会话
        limit: 返回的最大记录数
        
    返回：
        List[Card]: 需要复习的卡片列表
    """
    return db.query(Card).filter(
        Card.next_review_at <= datetime.now(timezone.utc)  # 只返回到期需要复习的卡片
    ).limit(limit).all()


async def update_review_progress(
    db: AsyncSession,
    *,
    db_card: Card,
    remembered: bool
) -> Card:
    """
    更新卡片的复习进度
    
    参数：
        db: 数据库会话
        db_card: 要更新的卡片
        remembered: 是否记住了卡片内容
        
    返回：
        Card: 更新后的卡片对象
    """
    now = datetime.now(timezone.utc)
    
    if remembered:
        # 如果是第一次复习，设置首次复习时间
        if db_card.review_count == 0:
            db_card.first_review_at = now
        
        # 增加复习次数
        db_card.review_count += 1
        
        # 计算下次复习时间
        # 使用首次复习时间作为基准，加上累计间隔天数
        total_days = 0
        for i in range(1, db_card.review_count + 1):
            # 查找当前复习次数对应的规则
            for rule in review_strategy.rules:
                if rule.min_count <= i <= rule.max_count:
                    total_days += rule.days
                    break
            else:
                # 如果没有找到匹配的规则，使用最后一个规则
                if review_strategy.rules:
                    total_days += review_strategy.rules[-1].days
                else:
                    total_days += 1
        
        # 使用首次复习时间加上累计间隔天数
        db_card.next_review_at = db_card.first_review_at + timedelta(days=total_days)
    else:
        # 如果忘记了，重置复习次数和首次复习时间
        db_card.review_count = 0
        db_card.first_review_at = None
        db_card.next_review_at = now
    
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def update_next_review(
    db: AsyncSession,
    *,
    db_card: Card,
    next_review_at: datetime
) -> Card:
    """
    修改卡片的下次复习时间
    
    参数:
        db: 数据库会话
        db_card: 要修改的卡片
        next_review_at: 新的下次复习时间（ISO 8601 格式，例如：2024-05-12T10:30:00Z）
        
    返回:
        Card: 更新后的卡片
    """
    # 确保时区信息被保留
    if next_review_at.tzinfo is None:
        next_review_at = next_review_at.replace(tzinfo=timezone.utc)
    else:
        # 如果有时区信息，转换为 UTC
        next_review_at = next_review_at.astimezone(timezone.utc)
    
    db_card.next_review_at = next_review_at
    await db.commit()
    await db.refresh(db_card)
    return db_card 