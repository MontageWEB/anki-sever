from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import card as crud_card
from app.schemas.card import (
    CardCreate,
    CardUpdate,
    CardResponse,
    CardListResponse
)

router = APIRouter()


@router.post("", response_model=CardResponse)
async def create_card(
    card_in: CardCreate,
    db: AsyncSession = Depends(deps.get_db)
) -> CardResponse:
    """创建新的知识卡片"""
    return await crud_card.create_card(db=db, card=card_in)


@router.get("", response_model=CardListResponse)
async def list_cards(
    db: AsyncSession = Depends(deps.get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None
) -> CardListResponse:
    """获取卡片列表，支持分页和搜索"""
    skip = (page - 1) * per_page
    cards, total = await crud_card.get_cards(
        db=db,
        skip=skip,
        limit=per_page,
        search=search
    )
    return CardListResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=cards
    )


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    db: AsyncSession = Depends(deps.get_db)
) -> CardResponse:
    """获取单个卡片的详细信息"""
    db_card = await crud_card.get_card(db=db, card_id=card_id)
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return db_card


@router.put("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: int,
    card_in: CardUpdate,
    db: AsyncSession = Depends(deps.get_db)
) -> CardResponse:
    """更新卡片内容"""
    db_card = await crud_card.get_card(db=db, card_id=card_id)
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return await crud_card.update_card(db=db, db_card=db_card, card_update=card_in)


@router.delete("/{card_id}", status_code=204)
async def delete_card(
    card_id: int,
    db: AsyncSession = Depends(deps.get_db)
) -> None:
    """删除指定卡片"""
    db_card = await crud_card.get_card(db=db, card_id=card_id)
    if db_card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    await crud_card.delete_card(db=db, db_card=db_card) 