from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session

from app.core.security import create_access_token, get_password_hash
from app.services.user import get_user_by_email, create_user
from app.deps import get_session
from app.schemas.user import UserCreate
from app.schemas.token import Token

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/register", response_model=Token)
def register(
    user_data: UserCreate,
    session: Session = Depends(get_session)
) -> Token:
    # Check if user already exists
    if existing_user := get_user_by_email(session=session, email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user (password hashing is handled in create_user)
    user = create_user(session=session, user=user_data)
    
    # Generate access token
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"type": "access"}
    )
    
    return Token(access_token=access_token)
