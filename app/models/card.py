"""
知识卡片模型模块
定义了知识卡片的数据结构和字段
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text

from app.models.base import Base


class Card(Base):
    """
    知识卡片模型
    
    字段说明：
    - question: 知识点/问题，最多100字
    - answer: 答案/解释，最多500字，支持富文本
    - review_count: 复习次数，从0开始
    - next_review_at: 下次复习时间
    """
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 知识点（问题）
    question = Column(
        String(100),
        nullable=False,
        index=True,
        comment="知识点"
    )
    
    # 答案，支持富文本
    answer = Column(
        String(500),  # 限制500字
        nullable=False,
        comment="答案"
    )
    
    # 复习次数
    review_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="复习次数"
    )
    
    # 下次复习时间
    next_review_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        comment="下次复习时间"
    )
    
    # 时间相关字段
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Card {self.id}: {self.question[:20]}...>" 