from typing import Optional

from sqlmodel import Session, select

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import InvalidCredentialsException


def create_user(*, session: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email, 
        password=hashed_password, 
        is_superuser=user.is_superuser
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_user_by_email(*, session: Session, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    user = session.exec(stmt).first()
    return user

def get_user_by_username(*, session: Session, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    user = session.exec(stmt).first()
    return user

def get_user_by_id(*, session: Session, user_id: int) -> Optional[User]:
    """Get a user by their ID"""
    stmt = select(User).where(User.id == user_id)
    user = session.exec(stmt).first()
    return user

def authenticate_user(*, session: Session, email: Optional[str] = None, username: Optional[str] = None, password: str) -> User:
    user = None
    
    if email:
        user = get_user_by_email(session=session, email=email)
    elif username:
        user = get_user_by_username(session=session, username=username)

    if not user:
        raise InvalidCredentialsException()
    
    if not verify_password(plain_password=password, hashed_password=user.password):
        raise InvalidCredentialsException()
    
    return user
