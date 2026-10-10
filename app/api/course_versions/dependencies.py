from fastapi import Depends
from database.db_connect.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.course_versions.service import CourseVersionService
from typing import Annotated


async def get_course_version_service(session: AsyncSession = Depends(get_db)):
    return CourseVersionService(session)

CourseVersionServiceDependency = Annotated[
    CourseVersionService, Depends(get_course_version_service)
]