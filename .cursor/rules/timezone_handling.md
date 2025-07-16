---
description: "时区处理最佳实践 - 解决 naive/aware datetime 比较问题"
globs: ["app/**/*.py", "tests/**/*.py"]
alwaysApply: true
---

# 时区处理最佳实践

## 🚨 核心问题

在获取待复习卡片时，发现没有显示今日的卡片。这是因为时区处理不当导致的。

### 根本原因
1. **MySQL DATETIME 字段不存储时区信息**
2. **SQLAlchemy 读取后可能变成 naive datetime（无 tzinfo）**
3. **与 aware datetime（有 tzinfo）比较时出错**
4. **错误信息：can't compare offset-naive and offset-aware datetimes**

## 🔧 解决方案

### 1. 统一使用 UTC 时区存储
```python
from datetime import datetime, timezone

# ✅ 正确：获取当前 UTC 时间
now = datetime.now(timezone.utc)

# ✅ 正确：创建带时区的时间对象
created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

# ❌ 错误：使用 naive datetime
now = datetime.now()  # 没有时区信息
```

### 2. 时区修正函数
```python
def fix_timezone_fields(obj):
    """修正对象时间字段的时区信息"""
    time_fields = ['created_at', 'updated_at', 'first_review_at', 'next_review_at']
    
    for field in time_fields:
        if hasattr(obj, field):
            value = getattr(obj, field)
            if value and value.tzinfo is None:
                setattr(obj, field, value.replace(tzinfo=timezone.utc))
```

### 3. 模型定义规范
```python
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone

class Card(Base):
    __tablename__ = "cards"
    
    # ✅ 正确：使用 lambda 包装时间函数
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    next_review_at = Column(DateTime, nullable=True)
```

## 🎯 关键方法修正

### 必须包含时区修正的方法

#### 1. 获取单个卡片
```python
async def get_card(db: AsyncSession, card_id: int, user_id: int) -> Optional[Card]:
    card = await db.get(Card, card_id)
    if card:
        fix_timezone_fields(card)  # 🔧 修正时区
    return card
```

#### 2. 获取卡片列表
```python
async def get_cards(db: AsyncSession, user_id: int, **filters) -> List[Card]:
    query = select(Card).filter(Card.user_id == user_id)
    result = await db.execute(query)
    cards = result.scalars().all()
    
    # 🔧 修正所有卡片的时区
    for card in cards:
        fix_timezone_fields(card)
    
    return cards
```

#### 3. 复习进度更新（最重要）
```python
async def update_review_progress(db: AsyncSession, card: Card, remembered: bool) -> Card:
    fix_timezone_fields(card)  # 🔧 修正时区
    
    now = datetime.now(timezone.utc)
    if card.first_review_at is None:
        card.first_review_at = now
    
    # 计算下次复习时间
    card.next_review_at = calculate_next_review(card, remembered)
    card.review_count += 1
    
    await db.commit()
    await db.refresh(card)
    return card
```

#### 4. 获取待复习卡片
```python
async def get_cards_to_review(db: AsyncSession, user_id: int) -> List[Card]:
    now = datetime.now(timezone.utc)
    query = select(Card).filter(
        Card.user_id == user_id,
        Card.next_review_at <= now  # 确保都是 UTC 时间
    )
    result = await db.execute(query)
    cards = result.scalars().all()
    
    # 🔧 修正时区
    for card in cards:
        fix_timezone_fields(card)
    
    return cards
```

## 📅 时间比较规范

### 正确的比较方式
```python
from datetime import datetime, timezone

# 获取当前 UTC 时间
now = datetime.now(timezone.utc)

# 获取今天的开始时间（UTC）
today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

# 查询今天及之前的待复习卡片
query = select(Card).filter(
    Card.user_id == user_id,
    Card.next_review_at <= now  # 确保都是 UTC 时间
).order_by(Card.next_review_at)
```

### 错误的时间比较
```python
# ❌ 错误：naive datetime 与 aware datetime 比较
from datetime import datetime

now = datetime.now()  # naive datetime
query = select(Card).filter(Card.next_review_at <= now)  # 错误！

# ❌ 错误：不同时区比较
from datetime import datetime, timezone
import pytz

utc_now = datetime.now(timezone.utc)
beijing_tz = pytz.timezone('Asia/Shanghai')
beijing_now = datetime.now(beijing_tz)

# 直接比较不同时区的时间
query = select(Card).filter(Card.next_review_at <= beijing_now)  # 错误！
```

## 📅 时间计算规范

### 复习时间计算
```python
def calculate_next_review(card: Card, remembered: bool) -> datetime:
    """计算下次复习时间"""
    now = datetime.now(timezone.utc)
    
    if not remembered:
        # 忘记：1小时后复习
        return now + timedelta(hours=1)
    
    # 记住：使用间隔重复算法
    intervals = [1, 3, 7, 14, 30, 90, 180, 365]  # 天数
    current_level = min(card.review_count, len(intervals) - 1)
    days = intervals[current_level]
    
    return now + timedelta(days=days)
```

### 时间范围查询
```python
def get_cards_by_date_range(
    db: AsyncSession, 
    user_id: int, 
    start_date: datetime, 
    end_date: datetime
) -> List[Card]:
    """按时间范围查询卡片"""
    # 确保时间范围有时区信息
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    
    query = select(Card).filter(
        Card.user_id == user_id,
        Card.created_at >= start_date,
        Card.created_at <= end_date
    )
    
    result = await db.execute(query)
    cards = result.scalars().all()
    
    # 修正时区
    for card in cards:
        fix_timezone_fields(card)
    
    return cards
```

## 🌐 前端时间处理

### UTC 到本地时间转换
```javascript
// 前端接收 UTC 时间，转换为本地时间显示
function formatDateTime(utcDateTime) {
    const date = new Date(utcDateTime);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 发送到后端时转换为 UTC
function toUTC(localDateTime) {
    const date = new Date(localDateTime);
    return date.toISOString();
}
```

## ⚠️ 注意事项

1. **创建新记录时，确保时间字段有时区信息**
2. **更新记录时，确保时间字段有时区信息**
3. **查询时，确保比较的时间都有时区信息**
4. **前端显示时，需要将 UTC 时间转换为用户所在时区**
5. **在所有 CRUD 操作中，读取数据库记录后立即修正时间字段的时区信息**
6. **特别注意 update_review_progress 等涉及时间比较的方法，必须修正时区信息**

## ⚠️ 常见错误和解决方案

### 错误1：时区比较错误
```python
# ❌ 错误：naive datetime 与 aware datetime 比较
from datetime import datetime

now = datetime.now()  # naive datetime
query = select(Card).filter(Card.next_review_at <= now)  # 错误！

# ✅ 解决方案：确保所有时间都有时区信息
def safe_time_comparison(time1, time2):
    """安全的时间比较"""
    if time1.tzinfo is None:
        time1 = time1.replace(tzinfo=timezone.utc)
    if time2.tzinfo is None:
        time2 = time2.replace(tzinfo=timezone.utc)
    return time1 <= time2
```

### 错误2：数据库时间字段问题
```python
# 问题：MySQL DATETIME 字段读取后变成 naive datetime

# ✅ 解决方案：在读取后立即修正
async def get_card_with_timezone_fix(db: AsyncSession, card_id: int):
    card = await db.get(Card, card_id)
    if card:
        fix_timezone_fields(card)  # 🔧 自动修正
    return card
```

### 错误3：前端时间显示错误
```python
# 问题：前端显示的时间不正确

# ✅ 解决方案：确保前后端时间格式一致
# 后端：返回 ISO 格式的 UTC 时间
return {
    "created_at": card.created_at.isoformat(),
    "next_review_at": card.next_review_at.isoformat() if card.next_review_at else None
}
```

## 🧪 测试规范

### 时区测试用例
```python
@pytest.mark.asyncio
async def test_timezone_handling(db: AsyncSession):
    """测试时区处理"""
    # 创建带时区的卡片
    card = Card(
        title="时区测试",
        content="测试时区处理",
        user_id=1,
        created_at=datetime.now(timezone.utc)
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    
    # 验证时区信息
    assert card.created_at.tzinfo is not None
    assert card.created_at.tzinfo == timezone.utc
    
    # 测试修正函数
    naive_time = datetime.now()
    card.created_at = naive_time
    fix_timezone_fields(card)
    assert card.created_at.tzinfo is not None

@pytest.mark.asyncio
async def test_time_comparison(db: AsyncSession):
    """测试时间比较"""
    now = datetime.now(timezone.utc)
    
    # 创建过去的卡片
    past_card = Card(
        title="过去的卡片",
        content="内容",
        user_id=1,
        next_review_at=now - timedelta(days=1)
    )
    
    # 创建未来的卡片
    future_card = Card(
        title="未来的卡片", 
        content="内容",
        user_id=1,
        next_review_at=now + timedelta(days=1)
    )
    
    db.add_all([past_card, future_card])
    await db.commit()
    
    # 查询待复习卡片（应该只包含过去的卡片）
    cards_to_review = await get_cards_to_review(db, user_id=1)
    assert len(cards_to_review) == 1
    assert cards_to_review[0].title == "过去的卡片"
```

## 📋 检查清单

### 开发时检查
- [ ] 所有时间字段使用 `datetime.now(timezone.utc)`
- [ ] 模型定义使用 `lambda: datetime.now(timezone.utc)`
- [ ] 查询前调用 `fix_timezone_fields()`
- [ ] 时间比较前确保时区一致
- [ ] 前端接收 UTC 时间并转换为本地时间

### 测试时检查
- [ ] 测试时区修正函数
- [ ] 测试时间比较逻辑
- [ ] 测试复习算法的时间计算
- [ ] 测试前端时间显示

## 🎯 最佳实践总结

1. **统一使用 UTC 时区存储**
2. **所有时间字段操作前检查时区信息**
3. **使用 fix_timezone_fields 函数修正时区**
4. **时间比较前确保时区一致**
5. **前端处理时进行时区转换**
6. **测试中验证时区处理逻辑**

## 📁 相关文件
- `app/crud/card.py` - 卡片CRUD操作
- `app/models/card.py` - 卡片模型定义
- `app/schemas/card.py` - 卡片数据验证
- `app/utils/timezone.py` - 时区工具函数
- `tests/test_timezone.py` - 时区处理测试 