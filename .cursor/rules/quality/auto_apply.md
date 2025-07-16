---
description: "自动应用规则 - AI助手自动执行代码修正"
globs: ["**/*.py"]
alwaysApply: true
---

# 自动应用规则

## 适用范围

允许AI在推理出合理的代码修正时，自动执行，无需每次征求用户确认。

### 适用场景
- 代码格式化和风格修正
- 类型注解添加
- 导入语句整理
- 简单的重构操作
- 错误修复
- 文档字符串添加

### 不适用场景
- 涉及业务逻辑的重大变更
- 可能影响系统稳定性的修改
- 需要用户确认的配置变更
- 涉及敏感信息的修改

## 自动执行原则

### 1. 安全性优先
- 只执行低风险的代码修正
- 保持代码功能不变
- 遵循项目编码规范

### 2. 可预测性
- 修正结果应该是可预测的
- 遵循明确的规则和标准
- 保持代码一致性

### 3. 可回滚性
- 修改应该是可回滚的
- 保留原始代码的逻辑
- 提供清晰的修改说明

## 具体规则

### 代码格式化
```python
# 自动应用 Black 格式化
# 自动调整行长度到79字符
# 自动整理导入语句

# 示例：自动格式化
def long_function_name(parameter1,parameter2,parameter3):
    return "结果:"+parameter1+","+str(parameter2)+","+str(parameter3)

# 自动修正为：
def long_function_name(
    parameter1: str,
    parameter2: int,
    parameter3: bool = True
) -> str:
    return f"结果: {parameter1}, {parameter2}, {parameter3}"
```

### 类型注解
```python
# 自动添加类型注解
def get_user_cards(user_id):
    return crud_card.get_cards_by_user_id(user_id)

# 自动修正为：
def get_user_cards(user_id: int) -> List[Card]:
    return crud_card.get_cards_by_user_id(user_id)
```

### 错误处理
```python
# 自动添加异常处理
def create_card(card_data):
    card = Card(**card_data)
    db.add(card)
    db.commit()

# 自动修正为：
async def create_card(card_data: dict) -> Card:
    try:
        card = Card(**card_data)
        db.add(card)
        await db.commit()
        await db.refresh(card)
        return card
    except Exception as e:
        await db.rollback()
        logger.error(f"创建卡片失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建卡片失败")
```

### 时区处理
```python
# 自动添加时区修正
def get_card(card_id):
    card = db.get(Card, card_id)
    return card

# 自动修正为：
async def get_card(card_id: int) -> Optional[Card]:
    card = await db.get(Card, card_id)
    if card:
        fix_timezone_fields(card)  # 自动添加时区修正
    return card
```

## 提示和警告

### 需要用户确认的情况
- 涉及业务逻辑的修改
- 可能影响性能的变更
- 涉及数据库结构的修改
- 涉及API接口的变更

### 自动执行的修改
- 代码格式化和风格修正
- 类型注解添加
- 导入语句整理
- 简单的重构操作
- 错误处理完善
- 文档字符串添加

## 执行标准

### 代码质量提升
- 提高代码可读性
- 增强类型安全性
- 改善错误处理
- 统一代码风格

### 项目规范遵循
- 遵循 PEP 8 规范
- 使用项目定义的命名约定
- 遵循项目的架构设计
- 保持代码一致性 