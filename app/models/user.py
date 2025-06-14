"""
用户表模型，支持微信一键注册/登录
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(64), unique=True, index=True, nullable=False, comment="微信openid")
    nickname = Column(String(64), nullable=True, comment="微信昵称")
    avatar = Column(String(256), nullable=True, comment="微信头像url")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False) 