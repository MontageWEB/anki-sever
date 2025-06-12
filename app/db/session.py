"""
数据库会话管理模块
主要职责：
1. 创建数据库引擎
2. 创建会话工厂
3. 提供数据库会话依赖
4. 定义 SQLAlchemy 基础模型类
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# 创建异步引擎
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,
    echo=True
)

# 创建异步会话工厂
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 创建基本模型类
# 所有的 ORM 模型都要继承这个基类
Base = declarative_base()

def get_db():
    """
    创建数据库会话的依赖函数
    
    这个函数会被 FastAPI 的依赖注入系统使用
    用法示例：
    ```
    @app.get("/items/")
    def read_items(db: Session = Depends(get_db)):
        items = db.query(Item).all()
        return items
    ```
    
    使用 yield 语法确保在请求结束时关闭数据库会话
    即使发生异常，也能保证数据库连接被正确关闭
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 