from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import card as crud_card
from app.schemas.card import (
    CardCreate,
    CardUpdate,
    CardResponse,
    CardListResponse,
    NextReviewUpdate,
    ReviewUpdate,
    SuccessResponse
)

router = APIRouter()


@router.post("", response_model=CardResponse)
async def create_card(
    card_in: CardCreate,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CardResponse:
    """创建新的知识卡片"""
    return await crud_card.create_card(db=db, card=card_in, user_id=user_id)


@router.get("", response_model=CardListResponse)
async def list_cards(
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id),
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    filter_tag: str = Query("all", description="筛选标签，可选值：all（全部）、today（今日复习）、tomorrow（明日复习）")
) -> CardListResponse:
    """获取卡片列表，支持分页、搜索和筛选标签"""
    skip = (page - 1) * per_page
    cards, total = await crud_card.get_cards(
        db=db,
        skip=skip,
        limit=per_page,
        search=search,
        user_id=user_id,
        filter_tag=filter_tag
    )
    return CardListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=cards
    )


@router.get("/review", response_model=CardListResponse)
async def get_cards_for_review(
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CardListResponse:
    """获取需要复习的卡片列表（返回所有需要复习的卡片，不分页）"""
    cards, total = await crud_card.get_cards_to_review(
        db=db,
        user_id=user_id,
        page=1,
        per_page=1000  # 设置一个足够大的值来获取所有卡片
    )
    return CardListResponse(
        total=total,
        page=1,  # 固定为第1页
        per_page=total,  # 每页数量等于总数量，这样前端就不会显示分页
        items=cards
    )


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CardResponse:
    """获取单个卡片的详细信息"""
    db_card = await crud_card.get_card(db=db, card_id=card_id, user_id=user_id)
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # 验证并修复数据一致性问题
    await crud_card.validate_and_fix_card_data(db=db, card=db_card)
    
    return db_card


@router.put("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: int,
    card_in: CardUpdate,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CardResponse:
    """更新卡片内容"""
    db_card = await crud_card.get_card(db=db, card_id=card_id, user_id=user_id)
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return await crud_card.update_card(db=db, db_card=db_card, card_update=card_in, user_id=user_id)


@router.delete("/{card_id}", status_code=200)
async def delete_card(
    card_id: int,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> SuccessResponse:
    """删除指定卡片"""
    db_card = await crud_card.get_card(db=db, card_id=card_id, user_id=user_id)
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    await crud_card.delete_card(db=db, db_card=db_card, user_id=user_id)
    return SuccessResponse(message="Card deleted successfully")


@router.put("/{card_id}/next-review", response_model=CardResponse)
async def update_next_review(
    card_id: int,
    next_review: NextReviewUpdate,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CardResponse:
    """修改卡片的下次复习时间，不影响复习次数和复习规则"""
    db_card = await crud_card.get_card(db=db, card_id=card_id, user_id=user_id)
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return await crud_card.update_next_review(
        db=db,
        db_card=db_card,
        next_review_at=next_review.next_review_at
    )


@router.post("/{card_id}/review", response_model=CardResponse)
async def update_review_status(
    card_id: int,
    review: ReviewUpdate,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int = Depends(deps.get_current_user_id)
) -> CardResponse:
    """更新卡片的复习状态"""
    try:
        db_card = await crud_card.get_card(db=db, card_id=card_id, user_id=user_id)
        if db_card is None:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # 在复习前验证并修复数据一致性问题
        await crud_card.validate_and_fix_card_data(db=db, card=db_card)
        
        return await crud_card.update_review_progress(
            db=db,
            db_card=db_card,
            remembered=review.remembered
        )
    except HTTPException:
        raise
    except Exception as e:
        # 记录详细错误信息
        print(f"Error in update_review_status: {str(e)}")
        print(f"Card ID: {card_id}, User ID: {user_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")