from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database.db_connect.db import get_db
from services.usage_log.service import UsageLogService


async def get_usage_log_service(session: AsyncSession = Depends(get_db)):
    return UsageLogService(session)


UsageLogServiceDependency = Annotated[UsageLogService, Depends(get_usage_log_service)]