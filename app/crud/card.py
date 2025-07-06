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
from app.models.review_rule import ReviewRule
from app.schemas.card import CardCreate, CardUpdate
from app.core.config import settings
from app.core.review_strategy import ConfigurableReviewStrategy

# 创建可配置的复习策略实例
review_strategy = ConfigurableReviewStrategy(settings.REVIEW_STRATEGY_RULES)

# 定义东八区时区
CST = timezone(timedelta(hours=8))

async def create_card(db: AsyncSession, card: CardCreate, user_id: int) -> Card:
    """创建新卡片"""
    # 使用东八区时间
    now = datetime.now(CST)
    
    db_card = Card(
        question=card.question,
        answer=card.answer,
        review_count=0,
        next_review_at=now,  # 新卡片立即可以复习
        created_at=now,
        updated_at=now,
        user_id=user_id,
    )
    db.add(db_card)
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def get_card(db: AsyncSession, card_id: int, user_id: int) -> Optional[Card]:
    """
    获取指定ID的卡片
    
    参数：
        db: 数据库会话
        card_id: 卡片ID
        user_id: 用户ID
        
    返回：
        Card | None: 卡片对象，如果不存在则返回None
    """
    result = await db.execute(select(Card).filter(Card.id == card_id, Card.user_id == user_id))
    return result.scalar_one_or_none()


async def get_cards(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    user_id: int
) -> tuple[list[Card], int]:
    """
    获取卡片列表
    
    参数:
        db: 数据库会话
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        search: 搜索关键词（可选）
        user_id: 用户ID
        
    返回:
        tuple[list[Card], int]: 卡片列表和总记录数
    """
    # 构建基础查询，添加按创建时间倒序排序
    query: Select = select(Card).filter(Card.user_id == user_id).order_by(Card.created_at.desc())
    count_query: Select = select(Card).filter(Card.user_id == user_id)

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
    card_update: CardUpdate,
    user_id: int
) -> Card:
    """更新卡片"""
    # 只允许更新属于当前用户的卡片
    if db_card.user_id != user_id:
        raise Exception('无权限操作他人卡片')
    for field, value in card_update.model_dump(exclude_unset=True).items():
        setattr(db_card, field, value)
    
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def delete_card(db: AsyncSession, *, db_card: Card, user_id: int) -> None:
    """删除卡片"""
    # 只允许删除属于当前用户的卡片
    if db_card.user_id != user_id:
        raise Exception('无权限操作他人卡片')
    await db.delete(db_card)
    await db.commit()


async def get_cards_to_review(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    per_page: int = 100
) -> tuple[list[Card], int]:
    """
    获取需要复习的卡片列表
    
    参数:
        db: 数据库会话
        user_id: 用户ID
        page: 页码，从1开始
        per_page: 每页数量
        
    返回:
        tuple[list[Card], int]: (卡片列表, 总数)
    """
    # 使用东八区时间
    now = datetime.now(CST)
    
    # 构建查询
    query = select(Card).where(
        Card.next_review_at <= now,
        Card.user_id == user_id
    ).order_by(Card.next_review_at.asc())
    
    # 计算总数
    count_query = select(func.count()).select_from(
        select(Card).where(
            Card.next_review_at <= now,
            Card.user_id == user_id
        ).subquery()
    )
    
    # 执行查询
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # 分页
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    cards = result.scalars().all()
    
    return cards, total


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
    now = datetime.now(CST)
    
    if remembered:
        # 如果是第一次复习，设置首次复习时间
        if db_card.review_count == 0 or db_card.first_review_at is None:
            # 确保设置的时间有时区信息
            if now.tzinfo is None:
                now = now.replace(tzinfo=CST)
            db_card.first_review_at = now
        # 增加复习次数
        db_card.review_count += 1
        # 计算下次复习时间，实时查 review_rules 表
        total_days = 0
        for i in range(1, db_card.review_count + 1):
            result = await db.execute(
                select(ReviewRule.interval_days).where(
                    ReviewRule.review_count == i,
                    ReviewRule.user_id == db_card.user_id
                )
            )
            interval_days = result.scalar_one_or_none()
            if interval_days is not None:
                total_days += interval_days
            else:
                # 没有找到规则，默认加 1 天
                total_days += 1
        
        # 优先使用 next_review_at 作为基准时间，如果不存在则使用 first_review_at
        base_time = db_card.next_review_at if db_card.next_review_at else db_card.first_review_at
        if base_time is None:
            # 如果 first_review_at 也不存在，使用创建时间
            base_time = db_card.created_at if db_card.created_at else now
        
        # 最终安全检查，确保 base_time 不为 None
        if base_time is None:
            base_time = now
        
        # 确保 base_time 有时区信息，如果没有则使用东八区
        if base_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=CST)
        
        # 确保计算出的时间也有时区信息
        next_review_time = base_time + timedelta(days=total_days)
        if next_review_time.tzinfo is None:
            next_review_time = next_review_time.replace(tzinfo=CST)
            
        db_card.next_review_at = next_review_time
    else:
        db_card.review_count = 0
        # 如果忘记，重置为初始状态，但保持创建时间作为首次复习时间的备选
        if db_card.first_review_at is None:
            db_card.first_review_at = db_card.created_at
        db_card.next_review_at = now
    db_card.updated_at = now
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
        next_review_at: 新的下次复习时间
        
    返回:
        Card: 更新后的卡片
    """
    # 确保使用东八区时间
    if next_review_at.tzinfo is None:
        next_review_at = next_review_at.replace(tzinfo=CST)
    
    db_card.next_review_at = next_review_at
    db_card.updated_at = datetime.now(CST)
    await db.commit()
    await db.refresh(db_card)
    return db_card 


async def get_card_by_question_answer(
    db: AsyncSession,
    user_id: int,
    question: str,
    answer: str
) -> Optional[Card]:
    """
    根据问题和答案获取卡片
    
    参数:
        db: 数据库会话
        user_id: 用户ID
        question: 问题
        answer: 答案
        
    返回:
        Card | None: 卡片对象，如果不存在则返回None
    """
    result = await db.execute(
        select(Card).filter(
            Card.user_id == user_id,
            Card.question == question,
            Card.answer == answer
        )
    )
    return result.scalar_one_or_none()


async def update_card_by_question_answer(
    db: AsyncSession,
    user_id: int,
    question: str,
    answer: str,
    new_data
) -> Card:
    """
    根据问题和答案更新卡片
    
    参数:
        db: 数据库会话
        user_id: 用户ID
        question: 问题
        answer: 答案
        new_data: 新的卡片数据
        
    返回:
        Card: 更新后的卡片
    """
    card = await get_card_by_question_answer(db, user_id, question, answer)
    if not card:
        raise Exception("卡片不存在")
    
    # 更新字段
    card.question = new_data.question
    card.answer = new_data.answer
    card.review_count = new_data.review_count
    card.next_review_at = new_data.next_review_at
    card.updated_at = datetime.now(CST)
    
    await db.commit()
    await db.refresh(card)
    return card


async def batch_create_cards_from_csv(
    db: AsyncSession,
    cards_data: List,
    user_id: int
) -> dict:
    """
    从CSV数据批量创建卡片
    
    参数:
        db: 数据库会话
        cards_data: CSV数据列表
        user_id: 用户ID
        
    返回:
        dict: 包含成功和失败统计的字典
    """
    success_count = 0
    failed_count = 0
    now = datetime.now(CST)
    
    for card_data in cards_data:
        try:
            # 获取时间字段，确保时区信息正确
            next_review_at = card_data.get_next_review_at_with_default(now)
            created_at = card_data.get_created_at_with_default(now)
            first_review_at = card_data.get_first_review_at()
            
            # 确保所有时间字段都有时区信息
            if next_review_at and next_review_at.tzinfo is None:
                next_review_at = next_review_at.replace(tzinfo=CST)
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=CST)
            if first_review_at and first_review_at.tzinfo is None:
                first_review_at = first_review_at.replace(tzinfo=CST)
            
            # 创建卡片，使用默认值策略
            db_card = Card(
                question=card_data.question,
                answer=card_data.answer,
                review_count=card_data.review_count,
                next_review_at=next_review_at,
                created_at=created_at,
                first_review_at=first_review_at,  # 允许NULL
                updated_at=now,
                user_id=user_id,
            )
            db.add(db_card)
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            print(f"创建卡片失败: {str(e)}")
    
    # 提交事务
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise Exception(f"批量导入事务失败: {str(e)}")
    
    return {
        "success": success_count,
        "failed": failed_count
    } 

async def validate_and_fix_card_data(db: AsyncSession, card: Card) -> bool:
    """
    验证并修复卡片数据的一致性问题
    
    参数:
        db: 数据库会话
        card: 要验证的卡片
        
    返回:
        bool: 是否进行了修复
    """
    fixed = False
    now = datetime.now(CST)
    
    # 1. 检查 first_review_at 的一致性
    if card.review_count > 0 and card.first_review_at is None:
        # 如果复习次数大于0但首次复习时间为空，设置为创建时间
        card.first_review_at = card.created_at if card.created_at else now
        fixed = True
    
    # 2. 确保所有时间字段都有时区信息
    if card.next_review_at and card.next_review_at.tzinfo is None:
        card.next_review_at = card.next_review_at.replace(tzinfo=CST)
        fixed = True
    
    if card.first_review_at and card.first_review_at.tzinfo is None:
        card.first_review_at = card.first_review_at.replace(tzinfo=CST)
        fixed = True
    
    if card.created_at and card.created_at.tzinfo is None:
        card.created_at = card.created_at.replace(tzinfo=CST)
        fixed = True
    
    if card.updated_at and card.updated_at.tzinfo is None:
        card.updated_at = card.updated_at.replace(tzinfo=CST)
        fixed = True
    
    # 3. 如果进行了修复，更新数据库
    if fixed:
        await db.commit()
        await db.refresh(card)
    
    return fixed 