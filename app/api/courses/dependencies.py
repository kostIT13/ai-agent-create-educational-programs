from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database.db_connect.db import get_db
from services.courses.service import CourseService


async def get_course_service(session: AsyncSession = Depends(get_db)):
    return CourseService(session)


CourseServiceDependency = Annotated[CourseService, Depends(get_course_service)]