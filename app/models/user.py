"""
用户表模型，支持微信一键注册/登录
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta

from app.models.base import Base

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(255), unique=True, index=True, nullable=False, comment="微信openid")
    nickname = Column(String(255), nullable=True, comment="用户昵称")
    avatar = Column(String(500), nullable=True, comment="用户头像")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 建立与卡片的关系
    cards = relationship("Card", back_populates="user") 