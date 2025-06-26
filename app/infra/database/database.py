from contextlib import asynccontextmanager
from typing import TypeVar

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.core.settings import settings

T = TypeVar("T")


class Database:
    _instance = None
    _connection: AsyncSession

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_db()

        return cls._instance

    def init_db(self):
        self.engine = create_async_engine(settings.db_settings.db_url)
        self._connection = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def get_session(self):
        # self._connection() — это AsyncSession
        async with self._connection() as session:
            yield session