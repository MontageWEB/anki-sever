"""
复习规则的 API 路由模块
提供了复习规则的增删改查接口
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Body

from app.api import deps
from app.crud import review_rule as crud_review_rule
from app.schemas.review_rule import (
    ReviewRule,
    ReviewRuleUpdate,
    ReviewRuleList,
    ReviewRuleUpdateListRequest
)

router = APIRouter()

@router.get("/", response_model=ReviewRuleList)
async def get_review_rules(
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id),
    skip: int = 0,
    limit: int = 100
) -> ReviewRuleList:
    """
    获取复习规则列表
    """
    rules = await crud_review_rule.get_review_rules(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    return ReviewRuleList(items=rules)

@router.put("/", response_model=ReviewRuleList)
async def update_review_rules(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id),
    body: ReviewRuleUpdateListRequest = Body(...)
) -> ReviewRuleList:
    """
    批量更新复习规则
    """
    rules = await crud_review_rule.update_review_rules(
        db=db,
        user_id=user_id,
        rules_in=body.rules
    )
    return ReviewRuleList(items=rules)

@router.post("/reset", response_model=ReviewRuleList)
async def reset_review_rules(
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> ReviewRuleList:
    """
    重置复习规则为默认值
    """
    rules = await crud_review_rule.reset_review_rules(db=db, user_id=user_id)
    return ReviewRuleList(items=rules) 