# API 开发规范

## 路由命名规范
1. 使用复数形式命名资源
   - 正确：`/cards`, `/review-settings`
   - 错误：`/card`, `/review-setting`

2. 使用连字符（-）连接多个单词
   - 正确：`/review-settings`, `/cards-to-review`
   - 错误：`/reviewSettings`, `/cardsToReview`

## 请求方法使用规范
- GET：获取资源
- POST：创建资源
- PUT：更新资源（需要提供完整资源）
- PATCH：部分更新资源（只需提供要更新的字段）
- DELETE：删除资源

## 响应规范
1. 状态码使用
   - 200：成功获取/更新资源
   - 201：成功创建资源
   - 204：成功删除资源
   - 400：请求参数错误
   - 404：资源不存在
   - 500：服务器内部错误

2. 错误响应格式
```json
{
    "detail": "错误信息"
}
```

## 分页规范
1. 查询参数
   - page：页码，从1开始
   - per_page：每页数量，默认20，最大100

2. 响应格式
```json
{
    "total": 100,
    "page": 1,
    "per_page": 20,
    "items": []
}
```

## 最佳实践
1. 使用异步函数处理请求
```python
@router.get("")
async def list_items(
    db: AsyncSession = Depends(deps.get_db)
):
    pass
```

2. 使用 Pydantic 模型进行数据验证
```python
class ItemCreate(BaseModel):
    name: str
    description: str | None = None
```

3. 使用依赖注入获取数据库会话
```python
from app.api import deps

@router.get("")
async def list_items(
    db: AsyncSession = Depends(deps.get_db)
):
    pass
```

4. 使用类型注解
```python
from typing import List, Optional

async def get_items(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None
) -> List[Item]:
    pass
```

## 常见问题解决方案
1. 跨域问题
   - 在 main.py 中配置 CORS 中间件
   - 指定允许的源、方法和头部

2. 数据库连接问题
   - 使用连接池管理连接
   - 正确关闭数据库连接
   - 使用异步连接避免阻塞

3. 性能优化
   - 使用适当的索引
   - 优化查询语句
   - 实现缓存机制 