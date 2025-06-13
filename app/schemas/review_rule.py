"""
复习规则的 Pydantic 模型模块
定义了复习规则的数据验证和序列化模型
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class ReviewRuleBase(BaseModel):
    """复习规则的基础模型"""
    review_count: int = Field(
        ...,
        description="复习次数",
        ge=1,
        le=20
    )
    interval_days: int = Field(
        ...,
        description="间隔天数",
        ge=1,
        le=365
    )


class ReviewRuleUpdate(ReviewRuleBase):
    """更新复习规则的请求模型"""
    pass


class ReviewRule(ReviewRuleBase):
    """复习规则的响应模型"""
    id: int = Field(..., description="规则ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ReviewRuleList(BaseModel):
    """复习规则列表的响应模型"""
    items: List[ReviewRule] = Field(..., description="规则列表")


class ReviewRuleUpdateListRequest(BaseModel):
    rules: List[ReviewRuleUpdate] = Field(..., description="批量更新的规则列表") 