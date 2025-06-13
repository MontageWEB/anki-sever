"""
复习规则的 API 路由模块
提供了复习规则的增删改查接口
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import review_rule as crud_review_rule
from app.schemas.review_rule import (
    ReviewRule,
    ReviewRuleUpdate,
    ReviewRuleList
)

router = APIRouter()


@router.get("/", response_model=ReviewRuleList)
async def get_review_rules(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
) -> ReviewRuleList:
    """
    获取复习规则列表
    """
    rules = await crud_review_rule.get_review_rules(
        db=db,
        skip=skip,
        limit=limit
    )
    return ReviewRuleList(items=rules)


@router.put("/", response_model=ReviewRuleList)
async def update_review_rules(
    *,
    db: AsyncSession = Depends(deps.get_db),
    rules_in: List[ReviewRuleUpdate]
) -> ReviewRuleList:
    """
    批量更新复习规则
    """
    rules = await crud_review_rule.update_review_rules(
        db=db,
        rules_in=rules_in
    )
    return ReviewRuleList(items=rules)


@router.post("/reset", response_model=ReviewRuleList)
async def reset_review_rules(
    db: AsyncSession = Depends(deps.get_db)
) -> ReviewRuleList:
    """
    重置复习规则为默认值
    """
    rules = await crud_review_rule.reset_review_rules(db=db)
    return ReviewRuleList(items=rules) 