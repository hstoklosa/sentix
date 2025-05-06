from typing import Optional

from sqlmodel import Session, select

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


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
    
    if not user or not verify_password(password, user.password):
        return None
    
    return user


def update_user(*, session: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
    user = get_user_by_id(session=session, user_id=user_id)
    
    if not user:
        return None
        
    # Update user attributes if provided in the update data
    if user_data.username is not None:
        user.username = user_data.username
        
    if user_data.email is not None:
        user.email = user_data.email
        
    if user_data.is_superuser is not None:
        user.is_superuser = user_data.is_superuser
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


def change_password(*, session: Session, user_id: int, current_password: str, new_password: str) -> bool:
    user = get_user_by_id(session=session, user_id=user_id)
    
    if not user:
        return False
    
    # Verify current password
    if not verify_password(current_password, user.password):
        return False
    
    # Update password
    user.password = get_password_hash(new_password)
    
    session.add(user)
    session.commit()
    
    return True
