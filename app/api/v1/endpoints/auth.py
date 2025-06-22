from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.api import deps
from app.core.config import settings
from app.core import wx, security
from app.crud import user as crud_user
from app.schemas.user import UserOut
from app.schemas.token import Token

router = APIRouter()

class WxLoginRequest(BaseModel):
    code: str = Field(..., description="微信登录临时凭证code")
    nickname: str = Field(None, description="微信昵称")
    avatar: str = Field(None, description="微信头像url")

class H5LoginRequest(BaseModel):
    nickname: str = Field("H5用户", description="用户昵称")
    avatar: str = Field("", description="用户头像url")

@router.post("/wx-login", response_model=Token)
async def wx_login(
    req: WxLoginRequest,
    db: AsyncSession = Depends(deps.get_db)
):
    # 测试账号逻辑
    if req.code == "test-code":
        openid = "test-openid"
        user = await crud_user.get_user_by_openid(db, openid)
        if not user:
            user = await crud_user.create_user(db, user_in=crud_user.UserCreate(
                openid=openid,
                nickname=req.nickname or "",
                avatar=req.avatar or ""
            ))
        token = security.create_access_token(str(user.id))
        return Token(access_token=token, token_type="bearer")
    # 正常微信流程
    wx_data = await wx.get_wx_openid(settings.WECHAT_APPID, settings.WECHAT_SECRET, req.code)
    if not wx_data or "openid" not in wx_data:
        raise HTTPException(status_code=400, detail="微信登录失败")
    openid = wx_data["openid"]
    user = await crud_user.get_user_by_openid(db, openid)
    if not user:
        user = await crud_user.create_user(db, user_in=crud_user.UserCreate(
            openid=openid,
            nickname=req.nickname,
            avatar=req.avatar
        ))
    token = security.create_access_token(str(user.id))
    return Token(access_token=token, token_type="bearer")

@router.post("/h5-login", response_model=Token)
async def h5_login(
    req: H5LoginRequest,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    H5环境专用登录接口
    不需要微信 code，直接创建或获取 H5 测试用户
    """
    # 使用固定的 H5 用户 openid
    h5_openid = "h5-test-openid"
    user = await crud_user.get_user_by_openid(db, h5_openid)
    if not user:
        user = await crud_user.create_user(db, user_in=crud_user.UserCreate(
            openid=h5_openid,
            nickname=req.nickname,
            avatar=req.avatar
        ))
    token = security.create_access_token(str(user.id))
    return Token(access_token=token, token_type="bearer") 