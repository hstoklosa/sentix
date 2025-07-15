from typing import Optional

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


async def create_user(*, session: AsyncSession, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email, 
        password=hashed_password, 
        is_superuser=user.is_superuser
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user_by_email(*, session: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    user = await session.execute(stmt)
    return user.scalar_one_or_none()


async def get_user_by_username(*, session: AsyncSession, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    user = await session.execute(stmt)
    return user.scalar_one_or_none()


async def get_user_by_id(*, session: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    user = await session.execute(stmt)
    return user.scalar_one_or_none()


async def authenticate_user(*, 
    session: AsyncSession, 
    email: Optional[str] = None, 
    username: Optional[str] = None, 
    password: str
) -> Optional[User]:
    user = None
    
    if email:
        user = await get_user_by_email(session=session, email=email)
    elif username:
        user = await get_user_by_username(session=session, username=username)
    
    if not user or not verify_password(password, user.password):
        return None
    
    return user
