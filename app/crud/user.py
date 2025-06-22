from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.crud import review_rule as crud_review_rule

async def get_user_by_openid(db: AsyncSession, openid: str) -> User | None:
    result = await db.execute(select(User).where(User.openid == openid))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    user = User(
        openid=user_in.openid,
        nickname=user_in.nickname or "",
        avatar=user_in.avatar or ""
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 为新用户自动初始化默认复习规则
    await crud_review_rule.reset_review_rules(db=db, user_id=user.id)
    
    return user 