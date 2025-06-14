"""
基础数据模型模块
定义所有数据模型的基类，提供通用字段和功能
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr

# 定义东八区时区
CST = timezone(timedelta(hours=8))

class Base(declarative_base()):
    """
    基础模型类，包含所有模型共用的字段
    
    特性：
    1. 自动生成表名（小写复数形式）
    2. 包含通用字段（id, created_at, updated_at）
    
    用法示例：
    ```python
    class User(BaseModel):
        name = Column(String(50))
        email = Column(String(100))
    ```
    """
    
    # 声明这是一个抽象基类，不会创建实际的数据库表
    __abstract__ = True

    # 主键ID
    # index=True：创建索引以加快查询
    # autoincrement=True：自动增长
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="主键ID"
    )
    
    # 创建时间
    # default=datetime.now(UTC)：默认使用当前UTC时间
    # nullable=False：不允许为空
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(CST))
    
    # 更新时间
    # onupdate=datetime.now(UTC)：记录更新时自动更新为当前时间
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(CST), onupdate=lambda: datetime.now(CST))

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