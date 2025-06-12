from fastapi import APIRouter

from app.api.v1.endpoints import cards, review_settings

api_router = APIRouter()

api_router.include_router(
    cards.router,
    prefix="/cards",
    tags=["cards"]
)

api_router.include_router(
    review_settings.router,
    prefix="/review-settings",
    tags=["review-settings"]
) 