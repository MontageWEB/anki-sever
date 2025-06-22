"""
复习规则的数据库模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.models.base import Base


class ReviewRule(Base):
    """复习规则表"""
    __tablename__ = "review_rules"

    id = Column(Integer, primary_key=True, index=True)
    review_count = Column(Integer, nullable=False, index=True)
    interval_days = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment="所属用户ID")

    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('user_id', 'review_count', name='uq_user_review_count'),
        {'mysql_engine': 'InnoDB'},
    ) 