from typing import Optional

from sqlmodel import Session, select

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import InvalidCredentialsException


def create_user(*, session: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
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

def authenticate_user(*, session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session=session, email=email)
    if not user:
        raise InvalidCredentialsException()
    
    if not verify_password(plain_password=password, hashed_password=user.password):
        raise InvalidCredentialsException()
    
    return user
