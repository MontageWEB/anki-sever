"""
基础数据模型模块
定义所有数据模型的基类，提供通用字段和功能
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr

Base = declarative_base()

class BaseModel(Base):
    """基础模型类"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @declared_attr
    def __tablename__(cls) -> str:
        """
        自动生成表名
        将模型类名转换为小写复数形式
        例如：
        - User -> users
        - Category -> categories
        """
        return cls.__name__.lower() + "s" 