from typing import Literal
from pydantic import BaseModel

from app.schemas.user import UserPublic


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenPayload(BaseModel):
    type: Literal["access", "refresh"]
    sub: str
    exp: int


class AuthResponse(BaseModel):
    token: Token
    user: UserPublic
