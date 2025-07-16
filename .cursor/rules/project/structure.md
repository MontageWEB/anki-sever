---
description: "项目结构规范 - 目录组织、模块设计、依赖管理"
globs: ["app/**/*.py", "tests/**/*.py"]
alwaysApply: true
---

# 项目结构规范

## 目录结构

### 标准项目结构
```
anki-sever/
├── app/                    # 应用主目录
│   ├── __init__.py
│   ├── main.py            # 应用入口
│   ├── api/               # API层
│   │   ├── __init__.py
│   │   ├── deps.py        # 依赖注入
│   │   └── v1/           # API版本
│   │       ├── __init__.py
│   │       ├── api.py     # 路由注册
│   │       └── endpoints/ # 接口实现
│   │           ├── auth.py
│   │           ├── cards.py
│   │           └── review_rules.py
│   ├── core/              # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py      # 配置管理
│   │   ├── security.py    # 安全相关
│   │   └── wx.py         # 微信API
│   ├── crud/              # 数据访问层
│   │   ├── __init__.py
│   │   ├── card.py
│   │   ├── user.py
│   │   └── review_rule.py
│   ├── db/                # 数据库配置
│   │   ├── __init__.py
│   │   ├── base_class.py  # 基础模型
│   │   ├── session.py     # 会话管理
│   │   └── init_db.py     # 数据库初始化
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── card.py
│   │   └── review_rule.py
│   ├── schemas/           # 数据验证
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── card.py
│   │   └── token.py
│   └── utils/             # 工具函数
│       ├── __init__.py
│       └── timezone.py
├── tests/                 # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── api/
│   ├── crud/
│   └── utils/
├── alembic/               # 数据库迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── scripts/               # 脚本文件
│   ├── start.sh
│   ├── backup_db.sh
│   └── init_db_manual.py
├── docs/                  # 文档
│   ├── api.md
│   └── PRD.md
├── requirements.txt       # 依赖管理
├── alembic.ini           # Alembic配置
└── README.md             # 项目说明
```

## 模块设计原则

### 分层架构
```python
# 1. API层 (app/api/)
# 职责：处理HTTP请求，参数验证，响应格式化
@router.post("")
async def create_card(card_in: CardCreate, db: AsyncSession = Depends(deps.get_db)):
    return await crud_card.create_card(db, card_in)

# 2. 业务逻辑层 (app/crud/)
# 职责：业务逻辑处理，数据操作
async def create_card(db: AsyncSession, card: CardCreate, user_id: int) -> Card:
    db_card = Card(**card.dict(), user_id=user_id)
    db.add(db_card)
    await db.commit()
    return db_card

# 3. 数据模型层 (app/models/)
# 职责：数据库模型定义
class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
```

### 依赖注入
```python
# app/api/deps.py
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import get_current_user_id

async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> int:
    """获取当前用户ID"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="无效的认证凭据"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except JWTError:
        raise credentials_exception
```

## 包结构规范

### __init__.py 文件
```python
# app/__init__.py
"""
Anki 服务器应用

一个基于 FastAPI 的卡片学习系统后端服务。
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# 导出主要模块
from .main import app
from .core.config import settings

__all__ = ["app", "settings"]
```

### 模块导入规范
```python
# 相对导入（推荐）
from .models.card import Card
from .schemas.card import CardCreate, CardResponse
from ..core.config import settings

# 绝对导入（避免循环导入时使用）
from app.models.card import Card
from app.schemas.card import CardCreate
```

## 配置管理

### 环境配置
```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+aiomysql://user:pass@localhost/anki_db"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 微信配置
    WECHAT_APPID: Optional[str] = None
    WECHAT_SECRET: Optional[str] = None
    
    # 应用配置
    PROJECT_NAME: str = "Anki Server"
    API_V1_STR: str = "/api/v1"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 环境变量管理
```bash
# .env.example
DATABASE_URL=mysql+aiomysql://user:password@localhost/anki_db
SECRET_KEY=your-secret-key-here
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret
```

## 路由组织

### API版本管理
```python
# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, cards, review_rules

api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(cards.router, prefix="/cards", tags=["卡片"])
api_router.include_router(review_rules.router, prefix="/review-rules", tags=["复习规则"])
```

### 路由文件组织
```python
# app/api/v1/endpoints/cards.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import card as crud_card
from app.schemas.card import CardCreate, CardResponse

router = APIRouter()

@router.post("", response_model=CardResponse)
async def create_card(
    card_in: CardCreate,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
):
    """创建卡片"""
    return await crud_card.create_card(db, card_in, user_id)

@router.get("", response_model=CardListResponse)
async def list_cards(
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """获取卡片列表"""
    return await crud_card.get_cards(db, user_id, page, per_page)
```

## 数据库设计

### 模型定义规范
```python
# app/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime, timezone

Base = declarative_base()

class BaseModel(Base):
    """基础模型类"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

### 模型关系定义
```python
# app/models/card.py
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Card(BaseModel):
    __tablename__ = "cards"
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系定义
    user = relationship("User", back_populates="cards")
    review_rules = relationship("ReviewRule", back_populates="card")
```

## 工具函数组织

### 工具模块设计
```python
# app/utils/__init__.py
"""
工具函数模块

包含项目中使用的各种工具函数和辅助方法。
"""

from .timezone import fix_timezone_fields, get_utc_now
from .validation import validate_email, validate_phone

__all__ = [
    "fix_timezone_fields",
    "get_utc_now", 
    "validate_email",
    "validate_phone"
]
```

### 工具函数实现
```python
# app/utils/timezone.py
from datetime import datetime, timezone
from typing import Any

def get_utc_now() -> datetime:
    """获取当前UTC时间"""
    return datetime.now(timezone.utc)

def fix_timezone_fields(obj: Any) -> None:
    """修正对象时间字段的时区信息"""
    time_fields = ['created_at', 'updated_at', 'first_review_at', 'next_review_at']
    
    for field in time_fields:
        if hasattr(obj, field):
            value = getattr(obj, field)
            if value and value.tzinfo is None:
                setattr(obj, field, value.replace(tzinfo=timezone.utc))
```

## 测试组织

### 测试目录结构
```
tests/
├── conftest.py           # 测试配置
├── api/                  # API测试
│   ├── test_auth.py
│   ├── test_cards.py
│   └── test_review_rules.py
├── crud/                 # CRUD测试
│   ├── test_card.py
│   └── test_user.py
└── utils/                # 工具函数测试
    └── test_timezone.py
```

### 测试配置
```python
# tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base_class import Base

@pytest_asyncio.fixture
async def db():
    """测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()
```

## 部署配置

### 脚本文件组织
```bash
# scripts/start.sh
#!/bin/bash
# 启动应用脚本

echo "启动 Anki 服务器..."

# 激活虚拟环境
source venv/bin/activate

# 检查数据库迁移
alembic upgrade head

# 启动应用
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 备份脚本
```bash
# scripts/backup_db.sh
#!/bin/bash
# 数据库备份脚本

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
DB_NAME="anki_db"

mkdir -p $BACKUP_DIR

echo "备份数据库 $DB_NAME..."
mysqldump -u root -p $DB_NAME | gzip > "$BACKUP_DIR/anki_backup_$DATE.sql.gz"

echo "备份完成: $BACKUP_DIR/anki_backup_$DATE.sql.gz"
```

## 文档组织

### API文档
```markdown
# docs/api.md
# API 接口文档

## 认证接口

### 微信登录
POST /api/v1/auth/wx-login

请求参数：
- code: string (必需) - 微信登录临时凭证
- nickname: string (可选) - 用户昵称
- avatar: string (可选) - 用户头像URL

响应：
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}
```
```

### 项目文档
```markdown
# README.md
# Anki 服务器

基于 FastAPI 的卡片学习系统后端服务。

## 功能特性

- 用户认证（微信登录）
- 卡片管理（CRUD操作）
- 复习系统（间隔重复算法）
- CSV导入导出

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. 初始化数据库
```bash
alembic upgrade head
```

4. 启动服务
```bash
uvicorn app.main:app --reload
```
``` 