from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database.db_connect.db import get_db
from services.users.service import UserService


async def get_user_service(session: AsyncSession = Depends(get_db)):
    return UserService(session)


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]