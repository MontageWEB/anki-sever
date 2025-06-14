from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    openid: str = Field(..., description="微信openid")
    nickname: str = Field(default="", description="微信昵称")
    avatar: str = Field(default="", description="微信头像url")

class UserCreate(UserBase):
    pass

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 