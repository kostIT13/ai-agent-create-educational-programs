from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database.db_connect.db import get_db
from services.events.service import EventService


async def get_event_service(session: AsyncSession = Depends(get_db)):
    return EventService(session)


EventServiceDependency = Annotated[EventService, Depends(get_event_service)]