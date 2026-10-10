import uuid
from typing import Annotated
from database.db_connect.db import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.feedback.schemas import (
    FeedbackCreate,
    FeedbackRead,
    FeedbackStats,
    FeedbackStatsRow,
)
from app.api.feedback.dependencies import FeedbackServiceDependency


router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
async def create_feedback(payload: FeedbackCreate, service: FeedbackServiceDependency):
    try:
        return await service.add(
            payload.course_id,
            payload.entity_id,
            payload.rating,
            comment=payload.comment,
            created_by=payload.created_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{feedback_id}", response_model=FeedbackRead)
async def get_feedback(feedback_id: uuid.UUID, service: FeedbackServiceDependency):
    feedback = await service.get(feedback_id)
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")
    return feedback


@router.get("/course/{course_id}", response_model=list[FeedbackRead])
async def list_course_feedback(
    course_id: uuid.UUID,
    service: FeedbackServiceDependency,
    entity_id: Annotated[str | None, Query(description="Фильтр по сущности")] = None,
):
    if entity_id is not None:
        return await service.list_by_entity(course_id, entity_id)
    return await service.list_by_course(course_id)


@router.get("/course/{course_id}/stats", response_model=FeedbackStats)
async def get_feedback_stats(course_id: uuid.UUID, service: FeedbackServiceDependency):
    rows = await service.avg_rating_by_entity(course_id)
    return FeedbackStats(
        course_id=course_id,
        items=[
            FeedbackStatsRow(entity_id=e, avg_rating=avg, count=count)
            for e, avg, count in rows
        ],
    )


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(feedback_id: uuid.UUID, service: FeedbackServiceDependency):
    deleted = await service.delete(feedback_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")
