from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database.db_connect.db import get_db
from services.jobs.service import JobService


async def get_job_service(session: AsyncSession = Depends(get_db)):
    return JobService(session)


JobServiceDependency = Annotated[JobService, Depends(get_job_service)]