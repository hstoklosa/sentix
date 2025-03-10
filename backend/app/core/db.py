from typing import Generator

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.core.config import settings
from app.services.user import get_user_by_email, create_user
from app.schemas.user import UserCreate

DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = get_user_by_email(session=session, email=settings.SUPERUSER_EMAIL)

        if not user:
            superuser = UserCreate(
                username=settings.SUPERUSER_USERNAME,
                email=settings.SUPERUSER_EMAIL,
                password=settings.SUPERUSER_PASSWORD,
                is_superuser=True,
            )
            create_user(session=session, user=superuser)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
