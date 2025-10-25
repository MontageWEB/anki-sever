"""
知识卡片的数据验证模型
使用 Pydantic 模型进行：
1. 请求数据验证
2. 响应数据序列化
3. API 文档生成
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CardBase(BaseModel):
    """
    卡片基础模型
    包含创建和更新卡片时共用的字段
    
    Field 参数说明：
    - ...: 表示该字段是必需的
    - max_length: 最大长度限制
    - description: 字段描述，用于API文档
    """
    question: str = Field(
        ...,
        max_length=100,
        description="知识点/问题"
    )
    answer: str = Field(
        ...,
        max_length=500,
        description="答案/解释"
    )


class CardCreate(CardBase):
    """
    创建卡片的请求模型
    继承自 CardBase，不需要额外的字段
    其他字段（如 review_count, next_review_at）会在创建时自动设置
    """
    pass


class CardUpdate(CardBase):
    """
    更新卡片的请求模型
    所有字段都是可选的，只更新提供的字段
    
    Optional 表示字段可以为 None
    """
    pass


class NextReviewUpdate(BaseModel):
    """
    修改下次复习时间的请求模型
    """
    next_review_at: datetime = Field(
        ...,
        description="下次复习时间（东八区时间）"
    )


class ReviewUpdate(BaseModel):
    """
    更新复习状态的请求模型
    """
    remembered: bool = Field(
        ...,
        description="是否记住了卡片内容"
    )


class CardInDBBase(CardBase):
    """
    数据库中的卡片基础模型
    包含从数据库读取的完整卡片信息
    
    Config.from_attributes = True 允许从 ORM 模型创建 Pydantic 模型
    """
    id: int = Field(..., description="卡片ID")
    review_count: int = Field(..., description="复习次数")
    next_review_at: datetime = Field(..., description="下次复习时间（东八区时间）")
    first_review_at: Optional[datetime] = Field(None, description="首次复习时间（东八区时间）")
    created_at: datetime = Field(..., description="创建时间（东八区时间）")
    updated_at: datetime = Field(..., description="更新时间（东八区时间）")
    user_id: int = Field(..., description="用户ID")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class CardResponse(BaseModel):
    """
    卡片响应模型
    用于 API 响应
    允许user_id为None，以支持访客模式
    """
    id: int = Field(..., description="卡片ID")
    question: str = Field(..., description="知识点/问题")
    answer: str = Field(..., description="答案/解释")
    review_count: int = Field(..., description="复习次数")
    next_review_at: datetime = Field(..., description="下次复习时间（东八区时间）")
    first_review_at: Optional[datetime] = Field(None, description="首次复习时间（东八区时间）")
    created_at: datetime = Field(..., description="创建时间（东八区时间）")
    updated_at: datetime = Field(..., description="更新时间（东八区时间）")
    user_id: Optional[int] = Field(None, description="用户ID")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class CardInDB(CardInDBBase):
    """
    数据库中的卡片完整模型
    包含从数据库读取的完整卡片信息
    
    Config.from_attributes = True 允许从 ORM 模型创建 Pydantic 模型
    """
    pass


class CardListResponse(BaseModel):
    """
    卡片列表响应模型
    """
    total: int
    page: int
    per_page: int
    items: list[CardResponse]


class SuccessResponse(BaseModel):
    """
    统一成功响应模型
    """
    success: bool = True
    message: str
    data: dict | None = None