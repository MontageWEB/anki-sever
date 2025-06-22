from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    openid: str = Field(..., description="微信openid")
    nickname: Optional[str] = Field(default="", description="微信昵称")
    avatar: Optional[str] = Field(default="", description="微信头像url")

class UserCreate(UserBase):
    pass

class UserOut(UserBase):
    id: int
    nickname: Optional[str] = Field(default="", description="微信昵称")
    avatar: Optional[str] = Field(default="", description="微信头像url")
    is_active: Optional[bool] = Field(default=True, description="用户是否激活")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")

    class Config:
        from_attributes = True 