"""
用户表模型，支持微信一键注册/登录
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base

class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(64), unique=True, index=True, nullable=False)
    nickname = Column(String(100), default="")
    avatar = Column(String(500), default="")
    is_active = Column(Boolean, default=True)

    # 建立与卡片的关系
    cards = relationship("Card", back_populates="user") 