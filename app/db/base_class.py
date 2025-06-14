"""
SQLAlchemy 基础模型类
所有数据库模型都应该继承 app.models.base.Base，不建议再用本文件。
"""

from typing import Any
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy 声明性基类
    提供了一些通用的功能：
    1. 自动生成表名（小写的类名）
    2. 创建和更新时间的自动更新
    """
    id: Any
    __name__: str
    
    # 生成表名
    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名为类名的小写形式"""
        return cls.__name__.lower()
    
    def __repr__(self) -> str:
        """返回模型的字符串表示"""
        attrs = []
        for key in self.__mapper__.columns.keys():
            value = getattr(self, key)
            if isinstance(value, datetime):
                value = value.isoformat()
            attrs.append(f"{key}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})" 