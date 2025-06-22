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

class H5LoginRequest(BaseModel):
    nickname: str = Field("H5用户", description="用户昵称")
    avatar: str = Field("", description="用户头像url")

@router.get("/me", response_model=UserOut)
async def get_current_user(
    current_user_id: int = Depends(deps.get_current_user_id),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    获取当前登录用户信息
    """
    try:
        user = await crud_user.get_user(db, current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("/me接口异常：", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"/me接口异常: {str(e)}")

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
                nickname="测试用户",
                avatar=""
            ))
        token = security.create_access_token(str(user.id))
        return Token(access_token=token, token_type="bearer")
    
    # 正常微信流程
    try:
        wx_data = await wx.get_wx_openid(settings.WECHAT_APPID, settings.WECHAT_SECRET, req.code)
        if not wx_data:
            raise HTTPException(status_code=400, detail="微信API调用失败")
        
        if "errcode" in wx_data:
            # 微信API返回错误
            error_msg = f"微信登录失败: {wx_data.get('errmsg', '未知错误')} (错误码: {wx_data.get('errcode')})"
            raise HTTPException(status_code=400, detail=error_msg)
        
        if "openid" not in wx_data:
            raise HTTPException(status_code=400, detail="微信登录失败: 未获取到openid")
        
        openid = wx_data["openid"]
        user = await crud_user.get_user_by_openid(db, openid)
        if not user:
            user = await crud_user.create_user(db, user_in=crud_user.UserCreate(
                openid=openid,
                nickname="微信用户",
                avatar=""
            ))
        token = security.create_access_token(str(user.id))
        return Token(access_token=token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"微信登录异常: {str(e)}")

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