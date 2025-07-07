"""
CSV导出相关的CRUD操作
"""

import csv
import io
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.card import Card
from datetime import timezone, timedelta

# 定义东八区时区
CST = timezone(timedelta(hours=8))


def format_datetime_for_csv(dt: Optional[datetime]) -> str:
    """
    格式化日期时间为CSV格式（YYYY-MM-DD HH:mm:ss）
    """
    if dt is None:
        return ""
    # 兼容字符串类型（如数据库里存的就是字符串）
    if isinstance(dt, str):
        # 尝试解析常见格式
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
            try:
                dt_obj = datetime.strptime(dt, fmt)
                dt = dt_obj
                break
            except Exception:
                continue
        else:
            return dt  # 兜底直接返回原字符串
    # 确保有时区信息
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CST)
    # 转换为东八区时间
    if dt.tzinfo != CST:
        dt = dt.astimezone(CST)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


async def get_user_cards_for_export(
    db: AsyncSession,
    user_id: int,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取用户的卡片数据用于导出
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        limit: 限制数量
        offset: 偏移量
        
    Returns:
        List[Dict]: 卡片数据列表
    """
    query = select(Card).where(Card.user_id == user_id).order_by(Card.created_at.desc())
    
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    
    result = await db.execute(query)
    cards = result.scalars().all()
    
    export_data = []
    for card in cards:
        export_data.append({
            "question": card.question,
            "answer": card.answer,
            "created_at": format_datetime_for_csv(card.created_at),
            "review_count": card.review_count,
            "next_review_at": format_datetime_for_csv(card.next_review_at)
        })
    
    return export_data


async def get_user_cards_count(db: AsyncSession, user_id: int) -> int:
    """
    获取用户的卡片总数
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        int: 卡片总数
    """
    result = await db.execute(
        select(func.count(Card.id)).where(Card.user_id == user_id)
    )
    return result.scalar()


def generate_csv_content(cards_data: List[Dict[str, Any]], include_headers: bool = True) -> str:
    """
    生成CSV内容
    
    Args:
        cards_data: 卡片数据列表
        include_headers: 是否包含表头
        
    Returns:
        str: CSV内容字符串
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    if include_headers:
        writer.writerow([
            "知识点",
            "答案", 
            "创建时间",
            "复习次数",
            "下次复习时间"
        ])
    
    # 写入数据行
    for card_data in cards_data:
        writer.writerow([
            card_data["question"],
            card_data["answer"],
            card_data["created_at"],
            card_data["review_count"],
            card_data["next_review_at"]
        ])
    
    return output.getvalue()


def save_csv_file(content: str, user_id: int) -> str:
    """
    保存CSV文件到本地
    
    Args:
        content: CSV内容
        user_id: 用户ID
        
    Returns:
        str: 文件路径
    """
    # 创建导出目录
    export_dir = "./exports"
    os.makedirs(export_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"anki_cards_user_{user_id}_{timestamp}.csv"
    filepath = os.path.join(export_dir, filename)
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath 