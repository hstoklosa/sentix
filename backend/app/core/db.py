from typing import Generator
import logging

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from app.core.config import settings
from app.services.user import get_user_by_email, create_user
from app.schemas.user import UserCreate
from app.core.exceptions import InvalidPasswordException

logger = logging.getLogger(__name__)

DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = get_user_by_email(session=session, email=settings.SUPERUSER_EMAIL)

        if not user:
            try:
                # Create superuser - password validation will be handled by UserCreate schema
                superuser = UserCreate(
                    username=settings.SUPERUSER_USERNAME,
                    email=settings.SUPERUSER_EMAIL,
                    password=settings.SUPERUSER_PASSWORD,
                    is_superuser=True,
                )
                create_user(session=session, user=superuser)
                logger.info(f"Superuser {settings.SUPERUSER_EMAIL} created successfully")
            except InvalidPasswordException as e:
                logger.error(f"Failed to create superuser: {e.detail}")
            except ValueError as e:
                logger.error(f"Failed to create superuser: {str(e)}")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
