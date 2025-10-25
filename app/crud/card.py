"""
知识卡片的数据库操作模块
实现了卡片的增删改查（CRUD）操作和复习进度管理
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict
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
from app.utils.timezone import fix_timezone_fields

# 导入UUID用于生成唯一标识符
import uuid

# 内存存储：会话ID到临时演示数据的映射
# 每个会话有自己独立的临时演示数据
TEMP_SESSION_DATA: Dict[str, Dict[str, List[Dict]]] = {}

# 生成会话ID的函数
def generate_session_id() -> str:
    return str(uuid.uuid4())

# 获取会话ID的函数（这里简化实现，实际应用中可能需要从请求上下文获取）
def get_session_id() -> str:
    # 注意：这是一个临时简化实现
    # 实际应用中应该从请求上下文或其他机制获取用户会话ID
    # 这里使用固定的会话ID进行演示
    return "default_guest_session"

# 创建可配置的复习策略实例
review_strategy = ConfigurableReviewStrategy(settings.REVIEW_STRATEGY_RULES)

# 默认演示数据模板，用于初始化会话的临时演示数据
DEFAULT_DEMO_CARDS_TEMPLATE = [
    {
        "id": 9991,
        "question": "【演示数据】什么是Anki记忆法？",
        "answer": "Anki是一种基于间隔重复原理的记忆辅助工具，通过科学的复习间隔帮助用户更高效地记忆和掌握知识。",
        "review_count": 2,
        "next_review_at": datetime.now(timezone.utc) + timedelta(hours=2),
        "created_at": datetime.now(timezone.utc) - timedelta(days=7),
        "updated_at": datetime.now(timezone.utc) - timedelta(days=1),
        "user_id": None,
        "first_review_at": datetime.now(timezone.utc) - timedelta(days=3)
    },
    {
        "id": 9992,
        "question": "【演示数据】间隔重复的基本原理是什么？",
        "answer": "间隔重复基于艾宾浩斯遗忘曲线，通过逐渐延长复习间隔的方式，在记忆即将衰减时进行复习，从而巩固记忆效果。",
        "review_count": 0,
        "next_review_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc) - timedelta(days=2),
        "updated_at": datetime.now(timezone.utc) - timedelta(days=2),
        "user_id": None,
        "first_review_at": None
    },
    {
        "id": 9993,
        "question": "【演示数据】如何创建有效的学习卡片？",
        "answer": "1. 保持问题简洁明了\n2. 答案尽量具体精确\n3. 一个卡片只包含一个知识点\n4. 使用问答形式而非陈述形式\n5. 结合实际应用场景",
        "review_count": 1,
        "next_review_at": datetime.now(timezone.utc) + timedelta(hours=12),
        "created_at": datetime.now(timezone.utc) - timedelta(days=5),
        "updated_at": datetime.now(timezone.utc) - timedelta(days=3),
        "user_id": None,
        "first_review_at": datetime.now(timezone.utc) - timedelta(days=3)
    },
    {
        "id": 9994,
        "question": "【演示数据】记忆的四个阶段是什么？",
        "answer": "1. 编码：将信息转化为可记忆的形式\n2. 存储：将编码后的信息保存到记忆系统\n3. 检索：从记忆系统中提取信息\n4. 巩固：通过重复加强记忆痕迹",
        "review_count": 3,
        "next_review_at": datetime.now(timezone.utc) + timedelta(days=1),
        "created_at": datetime.now(timezone.utc) - timedelta(days=10),
        "updated_at": datetime.now(timezone.utc) - timedelta(days=2),
        "user_id": None,
        "first_review_at": datetime.now(timezone.utc) - timedelta(days=8)
    },
    {
        "id": 9995,
        "question": "【演示数据】为什么需要登录才能保存我的卡片？",
        "answer": "登录可以确保您的数据安全保存并与您的账号绑定。只有登录后，您创建的卡片、复习进度等个人数据才能被持久化存储，并在不同设备间同步访问。",
        "review_count": 0,
        "next_review_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc) - timedelta(days=1),
        "updated_at": datetime.now(timezone.utc) - timedelta(days=1),
        "user_id": None,
        "first_review_at": None
    }
]

# 获取或初始化会话的临时演示数据
def get_or_init_session_cards(session_id: str) -> List[Dict]:
    """
    获取指定会话的临时演示数据，如果不存在则初始化
    """
    if session_id not in TEMP_SESSION_DATA or "cards" not in TEMP_SESSION_DATA[session_id]:
        # 初始化新会话的演示数据
        # 深拷贝默认模板，避免修改原模板
        import copy
        TEMP_SESSION_DATA[session_id] = {
            "cards": copy.deepcopy(DEFAULT_DEMO_CARDS_TEMPLATE),
            "last_updated": datetime.now(timezone.utc)
        }
    return TEMP_SESSION_DATA[session_id]["cards"]

# 更新会话的最后活动时间
def update_session_activity(session_id: str):
    """
    更新会话的最后活动时间
    """
    if session_id in TEMP_SESSION_DATA:
        TEMP_SESSION_DATA[session_id]["last_updated"] = datetime.now(timezone.utc)

# 清理过期会话数据
def cleanup_expired_sessions(max_age_hours: int = 24):
    """
    清理超过指定时间未活动的会话数据
    """
    now = datetime.now(timezone.utc)
    expired_sessions = []
    for session_id, session_data in TEMP_SESSION_DATA.items():
        if now - session_data["last_updated"] > timedelta(hours=max_age_hours):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del TEMP_SESSION_DATA[session_id]

def get_demo_card_by_id(card_id: int, session_id: str = None) -> Optional[Card]:
    """
    根据ID获取演示卡片
    """
    if session_id is None:
        session_id = get_session_id()
    
    session_cards = get_or_init_session_cards(session_id)
    update_session_activity(session_id)
    
    for card_data in session_cards:
        if card_data["id"] == card_id:
            card = Card(**card_data)
            fix_timezone_fields(card)
            return card
    return None

def get_demo_cards(skip: int = 0, limit: int = 20, search: Optional[str] = None, filter_tag: str = "all", session_id: str = None) -> Tuple[List[Card], int]:
    """
    获取演示卡片列表，支持搜索和筛选
    """
    if session_id is None:
        session_id = get_session_id()
    
    session_cards = get_or_init_session_cards(session_id)
    update_session_activity(session_id)
    
    # 过滤演示卡片
    filtered_cards = session_cards.copy()
    
    # 应用搜索
    if search:
        search_term = search.lower()
        filtered_cards = [
            card for card in filtered_cards 
            if search_term in card["question"].lower() or search_term in card["answer"].lower()
        ]
    
    # 应用筛选标签
    now = datetime.now(timezone.utc)
    if filter_tag == "today":
        filtered_cards = [card for card in filtered_cards if card["next_review_at"] < now + timedelta(days=1)]
    elif filter_tag == "tomorrow":
        filtered_cards = [
            card for card in filtered_cards 
            if card["next_review_at"] >= now + timedelta(days=1) 
            and card["next_review_at"] < now + timedelta(days=2)
        ]
    
    # 排序
    filtered_cards.sort(key=lambda x: (x["next_review_at"], x["created_at"]))
    
    # 分页
    total = len(filtered_cards)
    paginated_cards = filtered_cards[skip:skip + limit]
    
    # 转换为Card对象
    cards = [Card(**card_data) for card_data in paginated_cards]
    for card in cards:
        fix_timezone_fields(card)
    
    return cards, total

def get_demo_cards_to_review(session_id: str = None) -> Tuple[List[Card], int]:
    """
    获取需要复习的演示卡片
    """
    if session_id is None:
        session_id = get_session_id()
    
    session_cards = get_or_init_session_cards(session_id)
    update_session_activity(session_id)
    
    now = datetime.now(timezone.utc)
    review_cards = [card for card in session_cards if card["next_review_at"] <= now]
    review_cards.sort(key=lambda x: (x["next_review_at"], x["created_at"]))
    
    # 转换为Card对象
    cards = [Card(**card_data) for card_data in review_cards]
    for card in cards:
        fix_timezone_fields(card)
    
    return cards, len(cards)

# 为访客模式添加临时卡片操作函数
def create_demo_card(card_in: CardCreate, session_id: str = None) -> Card:
    """
    创建临时演示卡片
    """
    if session_id is None:
        session_id = get_session_id()
    
    session_cards = get_or_init_session_cards(session_id)
    
    # 生成新ID（负数，避免与数据库ID冲突）
    import random
    new_id = -random.randint(10000, 99999)
    
    now = datetime.now(timezone.utc)
    new_card_data = {
        "id": new_id,
        "question": f"【演示数据】{card_in.question}",
        "answer": card_in.answer,
        "review_count": 0,
        "next_review_at": now,
        "created_at": now,
        "updated_at": now,
        "user_id": None,
        "first_review_at": None
    }
    
    session_cards.append(new_card_data)
    update_session_activity(session_id)
    
    card = Card(**new_card_data)
    fix_timezone_fields(card)
    return card

def update_demo_card(card_id: int, card_update: CardUpdate, session_id: str = None) -> Optional[Card]:
    """
    更新临时演示卡片
    """
    if session_id is None:
        session_id = get_session_id()
    
    session_cards = get_or_init_session_cards(session_id)
    
    for card_data in session_cards:
        if card_data["id"] == card_id:
            # 更新卡片数据
            if card_update.question:
                # 保留【演示数据】标识
                if "【演示数据】" not in card_update.question:
                    card_data["question"] = f"【演示数据】{card_update.question}"
                else:
                    card_data["question"] = card_update.question
            if card_update.answer:
                card_data["answer"] = card_update.answer
            card_data["updated_at"] = datetime.now(timezone.utc)
            
            update_session_activity(session_id)
            
            card = Card(**card_data)
            fix_timezone_fields(card)
            return card
    
    return None

def delete_demo_card(card_id: int, session_id: str = None) -> bool:
    """
    删除临时演示卡片
    """
    if session_id is None:
        session_id = get_session_id()
    
    session_cards = get_or_init_session_cards(session_id)
    
    for i, card_data in enumerate(session_cards):
        if card_data["id"] == card_id:
            session_cards.pop(i)
            update_session_activity(session_id)
            return True
    
    return False

def update_demo_review_progress(card_id: int, remembered: bool, session_id: str = None) -> Optional[Card]:
    """
    更新临时演示卡片的复习进度
    """
    if session_id is None:
        session_id = get_session_id()
    
    session_cards = get_or_init_session_cards(session_id)
    
    for card_data in session_cards:
        if card_data["id"] == card_id:
            now = datetime.now(timezone.utc)
            
            if remembered:
                # 如果是第一次复习，设置首次复习时间
                if card_data["review_count"] == 0 or card_data["first_review_at"] is None:
                    card_data["first_review_at"] = now
                # 增加复习次数
                card_data["review_count"] += 1
                # 简单的复习间隔计算（1, 2, 4, 7, 15天）
                intervals = [1, 2, 4, 7, 15]
                interval_idx = min(card_data["review_count"] - 1, len(intervals) - 1)
                interval_days = intervals[interval_idx]
                # 计算下次复习时间
                card_data["next_review_at"] = now + timedelta(days=interval_days)
            else:
                # 如果忘记，重置复习进度
                card_data["review_count"] = 0
                card_data["next_review_at"] = now
            
            card_data["updated_at"] = now
            update_session_activity(session_id)
            
            card = Card(**card_data)
            fix_timezone_fields(card)
            return card
    
    return None

def update_demo_next_review(card_id: int, next_review_at: datetime, session_id: str = None) -> Optional[Card]:
    """
    修改临时演示卡片的下次复习时间
    """
    if session_id is None:
        session_id = get_session_id()
    
    session_cards = get_or_init_session_cards(session_id)
    
    # 确保使用 UTC 时间
    if next_review_at.tzinfo is None:
        next_review_at = next_review_at.replace(tzinfo=timezone.utc)
    
    for card_data in session_cards:
        if card_data["id"] == card_id:
            card_data["next_review_at"] = next_review_at
            card_data["updated_at"] = datetime.now(timezone.utc)
            update_session_activity(session_id)
            
            card = Card(**card_data)
            fix_timezone_fields(card)
            return card
    
    return None

# 创建可配置的复习策略实例
review_strategy = ConfigurableReviewStrategy(settings.REVIEW_STRATEGY_RULES)

async def create_card(db: AsyncSession, card: CardCreate, user_id: Optional[int] = None) -> Card:
    """创建新卡片"""
    # 如果是访客模式（user_id为None），创建临时演示卡片
    if user_id is None:
        return create_demo_card(card)
    
    # 登录用户创建数据库卡片
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
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


async def get_card(db: AsyncSession, card_id: int, user_id: Optional[int] = None) -> Optional[Card]:
    """
    根据ID获取单个卡片
    
    参数：
        db: 数据库会话
        card_id: 卡片ID
        user_id: 用户ID（可选，为None时返回演示卡片）
        
    返回：
        Card: 卡片对象，如果不存在则返回 None
    """
    # 未登录用户返回演示卡片
    if user_id is None:
        return get_demo_card_by_id(card_id)
    
    from datetime import datetime, timezone
    
    result = await db.execute(
        select(Card).filter(
            Card.id == card_id,
            Card.user_id == user_id
        )
    )
    card = result.scalar_one_or_none()
    
    # 修正卡片的时间字段时区信息
    if card:
        if card.created_at and card.created_at.tzinfo is None:
            card.created_at = card.created_at.replace(tzinfo=timezone.utc)
        if card.updated_at and card.updated_at.tzinfo is None:
            card.updated_at = card.updated_at.replace(tzinfo=timezone.utc)
        if card.first_review_at and card.first_review_at.tzinfo is None:
            card.first_review_at = card.first_review_at.replace(tzinfo=timezone.utc)
        if card.next_review_at and card.next_review_at.tzinfo is None:
            card.next_review_at = card.next_review_at.replace(tzinfo=timezone.utc)
    
    return card


async def get_cards(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    user_id: Optional[int] = None,
    filter_tag: str = "all"
) -> tuple[list[Card], int]:
    """
    获取卡片列表，支持搜索和筛选
    
    参数：
        db: 数据库会话
        skip: 跳过的记录数
        limit: 限制返回的记录数
        search: 搜索关键词
        user_id: 用户ID（可选，为None时返回演示卡片）
        filter_tag: 筛选标签，可选值：all（全部）、today（今日复习）、tomorrow（明日复习）
        
    返回：
        tuple: (卡片列表, 总数)
    """
    # 未登录用户返回演示卡片
    if user_id is None:
        return get_demo_cards(skip=skip, limit=limit, search=search, filter_tag=filter_tag)
    
    from datetime import datetime, timezone, timedelta
    
    # 构建基础查询
    query = select(Card).filter(Card.user_id == user_id)
    
    # 添加搜索条件
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Card.question.ilike(search_term),
                Card.answer.ilike(search_term)
            )
        )
    
    # 添加筛选条件
    if filter_tag == "today":
        # 今日复习：基于用户本地时间（北京时间）判断 - 包含已过期的卡片
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        now_beijing = datetime.now(beijing_tz)
        today_start_beijing = datetime(now_beijing.year, now_beijing.month, now_beijing.day, tzinfo=beijing_tz)
        today_end_beijing = today_start_beijing + timedelta(days=1)
        # 转换为UTC时间进行比较
        today_start_utc = today_start_beijing.astimezone(timezone.utc)
        today_end_utc = today_end_beijing.astimezone(timezone.utc)
        query = query.filter(Card.next_review_at < today_end_utc)  # 包含今天及之前的所有卡片（已过期+今天到期）
    elif filter_tag == "tomorrow":
        # 明日复习：基于用户本地时间（北京时间）判断
        from datetime import timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        now_beijing = datetime.now(beijing_tz)
        today_start_beijing = datetime(now_beijing.year, now_beijing.month, now_beijing.day, tzinfo=beijing_tz)
        tomorrow_start_beijing = today_start_beijing + timedelta(days=1)
        day_after_tomorrow_start_beijing = tomorrow_start_beijing + timedelta(days=1)
        # 转换为UTC时间进行比较
        tomorrow_start_utc = tomorrow_start_beijing.astimezone(timezone.utc)
        day_after_tomorrow_start_utc = day_after_tomorrow_start_beijing.astimezone(timezone.utc)
        query = query.filter(
            Card.next_review_at >= tomorrow_start_utc,
            Card.next_review_at < day_after_tomorrow_start_utc
        )
    # filter_tag == "all" 时不添加额外筛选条件
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 添加排序和分页
    query = query.order_by(Card.next_review_at.asc(), Card.created_at.asc())
    query = query.offset(skip).limit(limit)
    
    # 执行查询
    result = await db.execute(query)
    cards = result.scalars().all()
    
    # 修正所有卡片的时间字段时区信息
    for card in cards:
        if card.created_at and card.created_at.tzinfo is None:
            card.created_at = card.created_at.replace(tzinfo=timezone.utc)
        if card.updated_at and card.updated_at.tzinfo is None:
            card.updated_at = card.updated_at.replace(tzinfo=timezone.utc)
        if card.first_review_at and card.first_review_at.tzinfo is None:
            card.first_review_at = card.first_review_at.replace(tzinfo=timezone.utc)
        if card.next_review_at and card.next_review_at.tzinfo is None:
            card.next_review_at = card.next_review_at.replace(tzinfo=timezone.utc)
    
    return cards, total


async def update_card(
    db: AsyncSession,
    *,
    db_card: Card,
    card_update: CardUpdate,
    user_id: Optional[int] = None
) -> Card:
    """更新卡片"""
    # 如果是访客模式的卡片（db_card.user_id为None）
    if db_card.user_id is None:
        # 使用演示卡片更新函数
        updated_card = update_demo_card(db_card.id, card_update)
        if updated_card is None:
            raise Exception('演示卡片不存在')
        return updated_card
    
    # 登录用户的卡片，检查权限
    if user_id is None or db_card.user_id != user_id:
        raise Exception('无权限操作他人卡片')
    
    for field, value in card_update.model_dump(exclude_unset=True).items():
        setattr(db_card, field, value)
    
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def delete_card(db: AsyncSession, *, db_card: Card, user_id: Optional[int] = None) -> None:
    """删除卡片"""
    # 如果是访客模式的卡片（db_card.user_id为None）
    if db_card.user_id is None:
        # 使用演示卡片删除函数
        success = delete_demo_card(db_card.id)
        if not success:
            raise Exception('演示卡片不存在')
        return
    
    # 登录用户的卡片，检查权限
    if user_id is None or db_card.user_id != user_id:
        raise Exception('无权限操作他人卡片')
    
    await db.delete(db_card)
    await db.commit()


async def get_cards_to_review(
    db: AsyncSession,
    user_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 100
) -> tuple[list[Card], int]:
    """
    获取需要复习的卡片列表（已到期的卡片）
    
    参数：
        db: 数据库会话
        user_id: 用户ID（可选，为None时返回演示卡片）
        page: 页码
        per_page: 每页数量
        
    返回：
        tuple: (卡片列表, 总数)
    """
    # 未登录用户返回演示卡片
    if user_id is None:
        return get_demo_cards_to_review()
    
    from datetime import datetime, timezone, timedelta
    from app.utils.timezone import fix_timezone_fields
    # 计算偏移量
    skip = (page - 1) * per_page
    # 获取当前北京时间
    beijing_tz = timezone(timedelta(hours=8))
    now_beijing = datetime.now(beijing_tz)
    today_start_beijing = datetime(now_beijing.year, now_beijing.month, now_beijing.day, tzinfo=beijing_tz)
    today_end_beijing = today_start_beijing + timedelta(days=1)
    # 转换为UTC时间进行比较
    today_start_utc = today_start_beijing.astimezone(timezone.utc)
    today_end_utc = today_end_beijing.astimezone(timezone.utc)
    # 查询今日及之前的卡片（北京时间）- 包含已过期的卡片
    result = await db.execute(
        select(Card).filter(
            Card.user_id == user_id,
            Card.next_review_at < today_end_utc  # 包含今天及之前的所有卡片（已过期+今天到期）
        ).order_by(Card.next_review_at.asc(), Card.created_at.asc())
        .offset(skip).limit(per_page)
    )
    cards = result.scalars().all()
    # 修正所有卡片的时间字段时区信息
    for card in cards:
        fix_timezone_fields(card)
    # 获取总数
    count_result = await db.execute(
        select(func.count(Card.id)).filter(
            Card.user_id == user_id,
            Card.next_review_at < today_end_utc  # 包含今天及之前的所有卡片（已过期+今天到期）
        )
    )
    total = count_result.scalar()
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
    # 如果是访客模式的卡片（db_card.user_id为None）
    if db_card.user_id is None:
        # 使用演示卡片复习进度更新函数
        updated_card = update_demo_review_progress(db_card.id, remembered)
        if updated_card is None:
            raise Exception('演示卡片不存在')
        return updated_card
    
    from datetime import datetime, timezone
    
    # 修正时间字段的时区信息，确保所有时间字段都有 tzinfo=timezone.utc
    if db_card.created_at and db_card.created_at.tzinfo is None:
        db_card.created_at = db_card.created_at.replace(tzinfo=timezone.utc)
    if db_card.updated_at and db_card.updated_at.tzinfo is None:
        db_card.updated_at = db_card.updated_at.replace(tzinfo=timezone.utc)
    if db_card.first_review_at and db_card.first_review_at.tzinfo is None:
        db_card.first_review_at = db_card.first_review_at.replace(tzinfo=timezone.utc)
    if db_card.next_review_at and db_card.next_review_at.tzinfo is None:
        db_card.next_review_at = db_card.next_review_at.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    
    if remembered:
        # 如果是第一次复习，设置首次复习时间
        if db_card.review_count == 0 or db_card.first_review_at is None:
            # 确保设置的时间有时区信息
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            db_card.first_review_at = now
        # 增加复习次数
        db_card.review_count += 1
        # 计算下次复习时间，实时查 review_rules 表
        # 根据PRD要求：第20次复习之后的所有复习，将沿用用户设置的第20次复习间隔天数
        target_review_count = db_card.review_count
        # 如果复习次数超过20次，使用第20次的规则
        if target_review_count > 20:
            target_review_count = 20
            
        result = await db.execute(
            select(ReviewRule.interval_days).where(
                ReviewRule.review_count == target_review_count,
                ReviewRule.user_id == db_card.user_id
            )
        )
        interval_days = result.scalar_one_or_none()
        
        if interval_days is not None:
            total_days = interval_days
        else:
            # 没有找到规则，默认加 1 天
            total_days = 1
        
        # 优先使用 next_review_at 作为基准时间，如果不存在则使用 first_review_at
        base_time = db_card.next_review_at if db_card.next_review_at else db_card.first_review_at
        if base_time is None:
            # 如果 first_review_at 也不存在，使用创建时间
            base_time = db_card.created_at if db_card.created_at else now
        
        # 最终安全检查，确保 base_time 不为 None
        if base_time is None:
            base_time = now
        
        # 如果卡片已过期，强制使用当前时间作为基准时间
        if base_time < now:
            base_time = now
        
        # 确保 base_time 有时区信息，如果没有则使用 UTC
        if base_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=timezone.utc)
        
        # 确保计算出的时间也有时区信息
        next_review_time = base_time + timedelta(days=total_days)
        if next_review_time.tzinfo is None:
            next_review_time = next_review_time.replace(tzinfo=timezone.utc)
            
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
    # 如果是访客模式的卡片（db_card.user_id为None）
    if db_card.user_id is None:
        # 使用演示卡片下次复习时间更新函数
        updated_card = update_demo_next_review(db_card.id, next_review_at)
        if updated_card is None:
            raise Exception('演示卡片不存在')
        return updated_card
    
    from datetime import datetime, timezone
    # 确保使用 UTC 时间
    if next_review_at.tzinfo is None:
        next_review_at = next_review_at.replace(tzinfo=timezone.utc)
    
    db_card.next_review_at = next_review_at
    db_card.updated_at = datetime.now(timezone.utc)
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
    根据问题和答案获取卡片（如有多条只返回最早创建的那一条）
    """
    result = await db.execute(
        select(Card).filter(
            Card.user_id == user_id,
            Card.question == question,
            Card.answer == answer
        ).order_by(Card.created_at.asc())
    )
    cards = result.scalars().all()
    if not cards:
        return None
    return cards[0]


async def get_cards_by_question_answer(
    db: AsyncSession,
    user_id: int,
    question: str,
    answer: str
) -> list[Card]:
    """
    获取所有匹配问题和答案的卡片（同一用户）
    """
    result = await db.execute(
        select(Card).filter(
            Card.user_id == user_id,
            Card.question == question,
            Card.answer == answer
        )
    )
    return result.scalars().all()


async def update_card_by_question_answer(
    db: AsyncSession,
    user_id: int,
    question: str,
    answer: str,
    new_data
) -> Card:
    """
    根据问题和答案更新卡片（只覆盖一条，优先最早创建的那一条）
    """
    cards = await get_cards_by_question_answer(db, user_id, question, answer)
    if not cards:
        raise Exception("卡片不存在")
    # 只覆盖最早创建的那一条
    card = sorted(cards, key=lambda c: c.created_at)[0]
    card.question = new_data.question
    card.answer = new_data.answer
    card.review_count = new_data.review_count
    card.next_review_at = new_data.next_review_at or datetime.now(timezone.utc)
    card.updated_at = datetime.now(timezone.utc)
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
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    for card_data in cards_data:
        try:
            # 获取时间字段，确保时区信息正确
            next_review_at = card_data.get_next_review_at_with_default(now)
            created_at = card_data.get_created_at_with_default(now)
            first_review_at = card_data.get_first_review_at()
            
            # 确保所有时间字段都有时区信息
            if next_review_at and next_review_at.tzinfo is None:
                next_review_at = next_review_at.replace(tzinfo=timezone.utc)
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if first_review_at and first_review_at.tzinfo is None:
                first_review_at = first_review_at.replace(tzinfo=timezone.utc)
            
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
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    # 1. 检查 first_review_at 的一致性
    if card.review_count > 0 and card.first_review_at is None:
        # 如果复习次数大于0但首次复习时间为空，设置为创建时间
        card.first_review_at = card.created_at if card.created_at else now
        fixed = True
    
    # 2. 确保所有时间字段都有时区信息
    if card.next_review_at and card.next_review_at.tzinfo is None:
        card.next_review_at = card.next_review_at.replace(tzinfo=timezone.utc)
        fixed = True
    
    if card.first_review_at and card.first_review_at.tzinfo is None:
        card.first_review_at = card.first_review_at.replace(tzinfo=timezone.utc)
        fixed = True
    
    if card.created_at and card.created_at.tzinfo is None:
        card.created_at = card.created_at.replace(tzinfo=timezone.utc)
        fixed = True
    
    if card.updated_at and card.updated_at.tzinfo is None:
        card.updated_at = card.updated_at.replace(tzinfo=timezone.utc)
        fixed = True
    
    # 3. 如果进行了修复，更新数据库
    if fixed:
        await db.commit()
        await db.refresh(card)
    
    return fixed