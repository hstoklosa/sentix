from typing import Optional, Literal

from pydantic import BaseModel

from app.schemas.user import UserPublic


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    # refresh_token is not included as it will be sent as an HttpOnly cookie

class TokenPayload(BaseModel):
    sub: str
    type: Literal["access", "refresh"]
    exp: int

class AuthResponse(BaseModel):
    """Response schema for authentication endpoints that includes both token and user data"""
    token: Token
    user: UserPublic
