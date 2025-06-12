"""
复习设置的数据验证模型
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ReviewSettingResponse(BaseModel):
    """复习设置响应模型"""
    id: int
    review_count: int = Field(..., description="复习次数")
    interval_days: int = Field(..., description="间隔天数")
    description: str = Field(..., description="设置描述")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewSettingsListResponse(BaseModel):
    """复习设置列表响应模型"""
    items: list[ReviewSettingResponse] 