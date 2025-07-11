# 时区处理最佳实践

## 问题描述
在获取待复习卡片时，发现没有显示今日的卡片。这是因为时区处理不当导致的。

## 原因分析
1. 数据库中的时间字段使用 UTC 时区存储
2. 前端显示时需要考虑用户所在时区
3. 在比较时间时，需要确保时区一致
4. **新增：MySQL DATETIME 字段不存储时区信息，SQLAlchemy 读取后可能变成 naive datetime，与 aware datetime 比较时出错**

## 解决方案
1. 所有时间字段统一使用 UTC 时区存储
2. 在数据库操作时，使用 `datetime.now(timezone.utc)` 获取当前 UTC 时间
3. 在比较时间时，确保两个时间都是 UTC 时区
4. 在前端显示时，将 UTC 时间转换为用户所在时区
5. **新增：在所有时间字段操作前，检查并修正 naive datetime 为 aware datetime**

## 代码示例
```python
# 获取当前 UTC 时间
now = datetime.now(timezone.utc)

# 获取今天的开始时间（UTC）
today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

# 查询今天及之前的待复习卡片
query = (
    select(Card)
    .filter(Card.next_review_at <= now)  # 获取今天及之前的待复习卡片
    .order_by(Card.next_review_at)  # 按复习时间排序
)

# 新增：修正时间字段的时区信息
def fix_timezone_fields(card):
    """修正卡片时间字段的时区信息"""
    if card.created_at and card.created_at.tzinfo is None:
        card.created_at = card.created_at.replace(tzinfo=timezone.utc)
    if card.updated_at and card.updated_at.tzinfo is None:
        card.updated_at = card.updated_at.replace(tzinfo=timezone.utc)
    if card.first_review_at and card.first_review_at.tzinfo is None:
        card.first_review_at = card.first_review_at.replace(tzinfo=timezone.utc)
    if card.next_review_at and card.next_review_at.tzinfo is None:
        card.next_review_at = card.next_review_at.replace(tzinfo=timezone.utc)
```

## 注意事项
1. 创建新记录时，确保时间字段有时区信息
2. 更新记录时，确保时间字段有时区信息
3. 查询时，确保比较的时间都有时区信息
4. 前端显示时，需要将 UTC 时间转换为用户所在时区
5. **新增：在所有 CRUD 操作中，读取数据库记录后立即修正时间字段的时区信息**
6. **新增：特别注意 update_review_progress 等涉及时间比较的方法，必须修正时区信息**

## 关键方法修正
以下方法必须包含时区修正逻辑：
- `update_review_progress()` - 复习进度更新
- `get_cards_to_review()` - 获取待复习卡片
- `get_cards()` - 获取卡片列表
- `get_card()` - 获取单个卡片

## 相关文件
- app/crud/card.py
- app/models/card.py
- app/schemas/card.py 