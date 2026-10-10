from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database.db_connect.db import get_db
from services.references.service import ReferenceService


async def get_reference_service(session: AsyncSession = Depends(get_db)):
    return ReferenceService(session)


ReferenceServiceDependency = Annotated[ReferenceService, Depends(get_reference_service)]