from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/wx-login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with SessionLocal() as session:
        yield session 

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except JWTError:
        raise credentials_exception

async def get_current_user_id_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[int]:
    """
    可选的用户认证依赖
    当没有提供 token 时返回 None，而不是抛出异常
    适用于 H5 环境下的某些接口
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None 