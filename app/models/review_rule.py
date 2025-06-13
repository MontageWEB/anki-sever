"""
复习规则的数据库模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

from app.db.base_class import Base


class ReviewRule(Base):
    """复习规则表"""
    __tablename__ = "review_rules"

    id = Column(Integer, primary_key=True, index=True)
    review_count = Column(Integer, nullable=False, unique=True, index=True)
    interval_days = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) 