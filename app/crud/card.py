"""
知识卡片的数据库操作模块
实现了卡片的增删改查（CRUD）操作和复习进度管理
"""

from datetime import datetime, timezone
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
    """获取单个卡片"""
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
    """获取今日待复习的卡片"""
    now = datetime.now(timezone.utc)
    
    # 构建查询
    query = (
        select(Card)
        .filter(Card.next_review_at <= now)
        .order_by(Card.next_review_at)
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


def update_review_progress(
    db: Session,
    card_id: int,
    remembered: bool
) -> Optional[Card]:
    """
    更新卡片的复习进度
    
    参数：
        db: 数据库会话
        card_id: 卡片ID
        remembered: 是否记住了卡片内容
        
    返回：
        Card | None: 更新后的卡片对象，如果卡片不存在则返回None
    """
    db_card = get_card(db, card_id)
    if not db_card:
        return None
    
    if remembered:
        # 如果记住了，增加复习次数并计算下次复习时间
        db_card.review_count += 1
        db_card.next_review_at = review_strategy.calculate_next_review_time(
            db_card.review_count
        )
    else:
        # 如果忘记了，重置复习次数
        db_card.review_count = 0
        db_card.next_review_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_card)
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
        next_review_at: 新的下次复习时间
        
    返回:
        Card: 更新后的卡片
    """
    db_card.next_review_at = next_review_at
    await db.commit()
    await db.refresh(db_card)
    return db_card 