from typing import Generator

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.core.config import settings

DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

engine = create_engine(str(DATABASE_URL), echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
