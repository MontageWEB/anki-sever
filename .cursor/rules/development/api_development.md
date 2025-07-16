---
description: "API开发规范 - 路由设计、请求响应格式、错误处理"
globs: ["app/api/**/*.py", "app/schemas/**/*.py"]
alwaysApply: true
---

# API 开发规范

## 路由设计规范

### 路径命名
- 使用复数形式命名资源：`/cards`, `/review-rules`
- 使用连字符连接多词：`/review-settings`, `/cards-to-review`
- 路径不带斜杠结尾：`/cards` 而不是 `/cards/`

### HTTP 方法使用
- `GET`：获取资源
- `POST`：创建资源
- `PUT`：更新资源（完整更新）
- `PATCH`：部分更新资源
- `DELETE`：删除资源

### 状态码规范
- `200`：所有成功操作统一返回 200
- `400`：请求参数错误
- `401`：未认证
- `404`：资源不存在
- `500`：服务器内部错误

## 请求响应格式

### 成功响应格式
```python
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: dict | None = None
```

### 分页响应格式
```python
class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: List[Any]
```

### 错误响应格式
```json
{
    "detail": "错误信息"
}
```

## 认证规范

### Token 处理
- 使用 Bearer Token 认证
- Token 通过 Authorization 头部传递
- 所有需要认证的接口都要验证 Token

### 用户信息获取
```python
@router.get("/me", response_model=UserOut)
async def get_current_user(
    current_user_id: int = Depends(deps.get_current_user_id),
    db: AsyncSession = Depends(deps.get_db)
):
    pass
```

## 参数验证

### 查询参数
```python
@router.get("")
async def list_items(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None
):
    pass
```

### 请求体验证
```python
class ItemCreate(BaseModel):
    name: str = Field(..., description="名称")
    description: str | None = Field(None, description="描述")
```

## 数据库操作

### 异步会话使用
```python
@router.post("")
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
):
    pass
```

### 错误处理
```python
try:
    result = await crud_operation(db, data)
    return result
except HTTPException:
    raise
except Exception as e:
    logger.error(f"操作失败: {str(e)}")
    raise HTTPException(status_code=500, detail="内部服务器错误")
```

## 最佳实践

### 1. 路由注册
```python
# 在 api.py 中注册路由
router = APIRouter()
router.include_router(cards_router, prefix="/cards", tags=["cards"])
```

### 2. 响应模型
```python
class CardResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 3. 依赖注入
```python
from app.api import deps

@router.get("")
async def get_items(
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
):
    pass
```

## 常见问题解决方案

### 1. 跨域问题
```python
# main.py 中配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 时区处理
```python
# 所有时间字段使用 UTC
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### 3. 数据验证
```python
# 使用 Pydantic 进行数据验证
from pydantic import BaseModel, Field, validator
```

## 测试规范

### 接口测试
- 每个接口都要有对应的测试用例
- 测试正常流程和异常情况
- 使用 `httpx.AsyncClient` 进行测试

### 测试数据
- 使用测试专用的数据库
- 每个测试用例独立的数据环境
- 测试后自动清理数据 