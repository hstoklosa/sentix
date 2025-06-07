import contextlib
import logging
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from app.core.config import settings
from app.services.user import get_user_by_email, create_user
from app.schemas.user import UserCreate
from app.core.exceptions import InvalidPasswordException

logger = logging.getLogger(__name__)


# REF: https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html
class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


DATABASE_URL, ECHO_SQL = str(settings.SQLALCHEMY_DATABASE_URI), settings.ECHO_SQL
sessionmanager = DatabaseSessionManager(
    DATABASE_URL, {"echo": ECHO_SQL}
)


async def create_db_and_tables():
    async with sessionmanager.connect() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with sessionmanager.session() as session:
        user = await get_user_by_email(session=session, email=settings.SUPERUSER_EMAIL)
        if not user:
            try:
                superuser = UserCreate(
                    username=settings.SUPERUSER_USERNAME,
                    email=settings.SUPERUSER_EMAIL,
                    password=settings.SUPERUSER_PASSWORD,
                    is_superuser=True,
                )
                await create_user(session=session, user=superuser)
                logger.info(f"Superuser {settings.SUPERUSER_EMAIL} created successfully")
            except InvalidPasswordException as e:
                logger.error(f"Failed to create superuser: {e.detail}")
            except ValueError as e:
                logger.error(f"Failed to create superuser: {str(e)}")


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session
    