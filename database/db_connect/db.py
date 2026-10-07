from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator, Optional
from core.log_settings import logger 
from core.configs.db_config import db_settings


engine = create_async_engine(
    db_settings.POSTGRES_URL,
    echo=db_settings.DEBUG,
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0,
    },
)


async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
            logger.debug("Transaction committed")
        except Exception:
            await session.rollback()
            logger.exception("Transaction error")
            raise