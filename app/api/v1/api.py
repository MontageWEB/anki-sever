from fastapi import APIRouter

from app.api.v1.endpoints import cards, review_rules

api_router = APIRouter()

api_router.include_router(
    cards.router,
    prefix="/cards",
    tags=["cards"]
)

api_router.include_router(
    review_rules.router,
    prefix="/review-rules",
    tags=["复习规则"]
) 