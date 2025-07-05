from fastapi import APIRouter

from app.api.v1.endpoints import cards, review_rules, auth, csv_import

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

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

api_router.include_router(
    csv_import.router,
    prefix="/csv-import",
    tags=["CSV导入"]
) 