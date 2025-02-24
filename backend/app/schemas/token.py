from typing import Optional, Literal

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    # refresh_token is not included as it will be sent as an HttpOnly cookie

class TokenPayload(BaseModel):
    sub: str
    type: Literal["access", "refresh"]
    exp: int
