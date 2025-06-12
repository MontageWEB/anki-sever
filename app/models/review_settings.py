"""
复习设置的数据库模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.models.base import Base


class ReviewSetting(Base):
    """复习间隔设置模型"""
    __tablename__ = "review_settings"

    id = Column(Integer, primary_key=True, index=True)
    review_count = Column(Integer, nullable=False, comment="复习次数")
    interval_days = Column(Integer, nullable=False, comment="间隔天数")
    description = Column(String(100), nullable=False, comment="设置描述")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"ReviewSetting(id={self.id}, review_count={self.review_count}, interval_days={self.interval_days})" 