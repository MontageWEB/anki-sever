"""
知识卡片模型模块
定义了知识卡片的数据结构和字段
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.user import User  # 添加 User 模型的导入

# 定义东八区时区
CST = timezone(timedelta(hours=8))

class Card(Base):
    """
    知识卡片模型
    
    字段说明：
    - question: 知识点/问题，最多100字
    - answer: 答案/解释，最多500字，支持富文本
    - review_count: 复习次数，从0开始
    - first_review_at: 首次复习时间，用于计算下次复习时间
    - next_review_at: 下次复习时间
    """
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 知识点（问题）
    question = Column(
        String(255),
        nullable=False,
        index=True,
        comment="知识点"
    )
    
    # 答案，支持富文本
    answer = Column(
        String(1000),  # 限制1000字
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
    
    # 首次复习时间
    first_review_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="首次复习时间"
    )
    
    # 下次复习时间
    next_review_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(CST),
        nullable=False,
        index=True,
        comment="下次复习时间"
    )
    
    # 时间相关字段
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(CST),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(CST),
        onupdate=lambda: datetime.now(CST),
        nullable=False
    )

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment="所属用户ID")

    # 建立与用户的关系
    user = relationship("User", back_populates="cards")

    def __repr__(self) -> str:
        return f"<Card {self.id}: {self.question[:20]}...>" 