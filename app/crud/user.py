from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate

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
    return user 