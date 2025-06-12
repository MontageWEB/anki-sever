"""
知识卡片的 API 路由模块
提供卡片的 HTTP API 接口，包括：
1. 卡片的增删改查
2. 卡片列表查询（支持分页和搜索）
3. 复习相关操作
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import card as card_crud
from app.schemas.card import CardCreate, CardUpdate, CardResponse
from app.db.session import get_db

# 创建路由器
router = APIRouter()


@router.post("/", response_model=CardResponse)
def create_card(
    card: CardCreate,
    db: Session = Depends(get_db)
):
    """
    创建新卡片
    
    请求体：
    - question: 知识点/问题
    - answer: 答案/解释
    
    返回：
    - 201: 创建的卡片信息
    """
    return card_crud.create_card(db=db, card=card)


@router.get("/{card_id}", response_model=CardResponse)
def get_card(
    card_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定ID的卡片
    
    路径参数：
    - card_id: 卡片ID
    
    返回：
    - 200: 卡片信息
    - 404: 卡片不存在
    """
    db_card = card_crud.get_card(db=db, card_id=card_id)
    if db_card is None:
        raise HTTPException(status_code=404, detail="卡片不存在")
    return db_card


@router.get("/", response_model=List[CardResponse])
def get_cards(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回的最大记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取卡片列表
    
    查询参数：
    - skip: 跳过的记录数（用于分页）
    - limit: 返回的最大记录数（1-100）
    - search: 搜索关键词（可选）
    
    返回：
    - 200: 卡片列表
    """
    return card_crud.get_cards(db=db, skip=skip, limit=limit, search=search)


@router.get("/review/today", response_model=List[CardResponse])
def get_cards_for_review(
    limit: int = Query(100, ge=1, le=100, description="返回的最大记录数"),
    db: Session = Depends(get_db)
):
    """
    获取今日需要复习的卡片
    
    查询参数：
    - limit: 返回的最大记录数（1-100）
    
    返回：
    - 200: 需要复习的卡片列表
    """
    return card_crud.get_cards_for_review(db=db, limit=limit)


@router.put("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    card_update: CardUpdate,
    db: Session = Depends(get_db)
):
    """
    更新卡片信息
    
    路径参数：
    - card_id: 卡片ID
    
    请求体：
    - question: 知识点/问题（可选）
    - answer: 答案/解释（可选）
    - next_review_at: 下次复习时间（可选）
    
    返回：
    - 200: 更新后的卡片信息
    - 404: 卡片不存在
    """
    db_card = card_crud.update_card(db=db, card_id=card_id, card_update=card_update)
    if db_card is None:
        raise HTTPException(status_code=404, detail="卡片不存在")
    return db_card


@router.delete("/{card_id}")
def delete_card(
    card_id: int,
    db: Session = Depends(get_db)
):
    """
    删除卡片
    
    路径参数：
    - card_id: 卡片ID
    
    返回：
    - 200: 删除成功
    - 404: 卡片不存在
    """
    success = card_crud.delete_card(db=db, card_id=card_id)
    if not success:
        raise HTTPException(status_code=404, detail="卡片不存在")
    return {"message": "卡片已删除"}


@router.post("/{card_id}/review")
def review_card(
    card_id: int,
    remembered: bool,
    db: Session = Depends(get_db)
):
    """
    更新卡片复习进度
    
    路径参数：
    - card_id: 卡片ID
    
    查询参数：
    - remembered: 是否记住了卡片内容
    
    返回：
    - 200: 更新成功
    - 404: 卡片不存在
    
    说明：
    - 如果 remembered=true，增加复习次数并更新下次复习时间
    - 如果 remembered=false，重置复习次数，设置为立即复习
    """
    db_card = card_crud.update_review_progress(
        db=db,
        card_id=card_id,
        remembered=remembered
    )
    if db_card is None:
        raise HTTPException(status_code=404, detail="卡片不存在")
    return {"message": "复习进度已更新"} 