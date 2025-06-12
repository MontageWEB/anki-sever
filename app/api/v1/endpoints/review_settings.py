"""
复习设置的 API 路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import review_settings as crud_review_settings
from app.schemas.review_settings import ReviewSettingsListResponse

router = APIRouter()


@router.get("", response_model=ReviewSettingsListResponse)
async def get_review_settings(
    db: AsyncSession = Depends(deps.get_db)
) -> ReviewSettingsListResponse:
    """获取所有复习间隔设置"""
    settings = await crud_review_settings.get_review_settings(db=db)
    return ReviewSettingsListResponse(items=settings) 