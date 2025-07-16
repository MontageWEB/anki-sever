---
description: "代码风格规范 - 格式化、命名、注释、类型注解"
globs: ["**/*.py"]
alwaysApply: true
---

# 代码风格规范

## 格式化规范

### Black 配置
```toml
# pyproject.toml
[tool.black]
line-length = 79
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### 行长度限制
- 最大行长度：79 字符
- 长行使用括号换行
- 字符串使用 f-string

```python
# 正确示例
def long_function_name(
    parameter1: str,
    parameter2: int,
    parameter3: bool = True
) -> str:
    return f"结果: {parameter1}, {parameter2}, {parameter3}"

# 错误示例
def long_function_name(parameter1: str, parameter2: int, parameter3: bool = True) -> str:
    return "结果: " + parameter1 + ", " + str(parameter2) + ", " + str(parameter3)
```

## 命名规范

### 变量和函数命名
```python
# 变量：小写字母 + 下划线
user_id = 123
card_title = "Python基础"

# 函数：小写字母 + 下划线
def get_user_by_id(user_id: int) -> User:
    pass

def create_new_card(title: str, content: str) -> Card:
    pass

# 常量：大写字母 + 下划线
MAX_CARDS_PER_USER = 1000
DEFAULT_PAGE_SIZE = 20
```

### 类命名
```python
# 类名：大驼峰命名
class User(Base):
    pass

class CardManager:
    pass

class ReviewRuleService:
    pass
```

### 模块命名
```python
# 模块名：小写字母 + 下划线
# 文件名：user.py, card_manager.py, review_rules.py
```

## 注释规范

### 文档字符串
```python
def create_card(db: AsyncSession, card_data: dict, user_id: int) -> Card:
    """
    创建新的知识卡片
    
    Args:
        db: 数据库会话
        card_data: 卡片数据字典
        user_id: 用户ID
        
    Returns:
        Card: 创建的卡片对象
        
    Raises:
        HTTPException: 当创建失败时抛出
    """
    pass
```

### 行内注释
```python
# 获取当前UTC时间
now = datetime.now(timezone.utc)

# 修正时区信息（MySQL DATETIME 字段不存储时区）
if card.created_at and card.created_at.tzinfo is None:
    card.created_at = card.created_at.replace(tzinfo=timezone.utc)
```

### 类型注解
```python
from typing import List, Optional, Dict, Any
from datetime import datetime

def get_cards(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[Card]:
    pass

async def update_review_progress(
    db: AsyncSession,
    card: Card,
    remembered: bool
) -> Card:
    pass
```

## 导入规范

### 导入顺序
```python
# 1. 标准库导入
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional

# 2. 第三方库导入
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

# 3. 本地应用导入
from app.api import deps
from app.crud import card as crud_card
from app.schemas.card import CardCreate, CardResponse
```

### 导入方式
```python
# 推荐：明确导入
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

# 避免：通配符导入
from fastapi import *
from sqlalchemy import *
```

## 错误处理规范

### 异常处理
```python
try:
    result = await crud_operation(db, data)
    return result
except HTTPException:
    # 重新抛出 HTTP 异常
    raise
except Exception as e:
    # 记录详细错误信息
    logger.error(f"操作失败: {str(e)}")
    logger.error(f"错误详情: {traceback.format_exc()}")
    raise HTTPException(status_code=500, detail="内部服务器错误")
```

### 日志记录
```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.info("开始执行操作")
    try:
        # 操作逻辑
        logger.info("操作执行成功")
    except Exception as e:
        logger.error(f"操作失败: {str(e)}")
        raise
```

## 代码组织

### 函数长度
- 单个函数不超过 50 行
- 复杂逻辑拆分为多个小函数
- 使用描述性的函数名

### 类设计
```python
class CardService:
    """卡片服务类，处理卡片相关的业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_card(self, card_data: dict, user_id: int) -> Card:
        """创建卡片"""
        pass
    
    async def get_cards(self, user_id: int, **filters) -> List[Card]:
        """获取卡片列表"""
        pass
```

## 性能优化

### 数据库查询
```python
# 使用 select 而不是 query
from sqlalchemy import select

# 正确
query = select(Card).filter(Card.user_id == user_id)

# 错误
query = db.query(Card).filter(Card.user_id == user_id)
```

### 异步编程
```python
# 使用 async/await
async def get_user_cards(user_id: int) -> List[Card]:
    cards = await crud_card.get_cards_by_user_id(user_id)
    return cards

# 避免同步阻塞操作
# 错误示例
def get_user_cards(user_id: int) -> List[Card]:
    cards = crud_card.get_cards_by_user_id(user_id)  # 同步操作
    return cards
```

## 安全检查

### 输入验证
```python
from pydantic import BaseModel, Field, validator

class CardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('标题不能为空')
        return v.strip()
```

### SQL 注入防护
```python
# 使用参数化查询
query = select(Card).filter(Card.user_id == user_id)

# 避免字符串拼接
# 错误示例
query = f"SELECT * FROM cards WHERE user_id = {user_id}"
```

## 测试规范

### 测试函数命名
```python
def test_create_card_success():
    """测试创建卡片成功"""
    pass

def test_create_card_missing_title():
    """测试创建卡片缺少标题"""
    pass

def test_get_cards_with_pagination():
    """测试分页获取卡片列表"""
    pass
```

### 测试数据
```python
@pytest.fixture
def sample_card_data():
    """测试卡片数据"""
    return {
        "title": "测试卡片",
        "content": "测试内容",
        "user_id": 1
    }
``` 