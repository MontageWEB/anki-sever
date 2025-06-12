from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import expression

from app.models.base import Base


class ReviewSettings(Base):
    """复习设置表"""
    __tablename__ = "review_settings"

    id = Column(Integer, primary_key=True, index=True)
    review_count = Column(
        Integer,
        nullable=False,
        comment="第几次复习"
    )
    interval_days = Column(
        Integer,
        nullable=False,
        comment="复习间隔天数"
    )
    description = Column(
        String(255),
        nullable=True,
        comment="设置描述"
    )
    is_active = Column(
        Boolean, 
        nullable=False, 
        server_default=expression.true(),
        comment="是否启用"
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
        return f"<ReviewSettings(review_count={self.review_count}, interval_days={self.interval_days})>" 