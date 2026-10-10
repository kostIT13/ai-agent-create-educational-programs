from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from database.db_connect.db import get_db
from services.feedback.service import FeedbackService


async def get_feedback_service(session: AsyncSession = Depends(get_db)):
    return FeedbackService(session)


FeedbackServiceDependency = Annotated[FeedbackService, Depends(get_feedback_service)]