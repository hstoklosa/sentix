from pydantic import EmailStr
from sqlmodel import SQLModel, Field

# USER MODELS
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_superuser: bool = False

class User(UserBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)
    password: str

class UserPublic(UserBase):
    id: int

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=64)