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
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    openid = Column(String(64), unique=True, index=True)

    # 建立与卡片的关系
    cards = relationship("Card", back_populates="user") 