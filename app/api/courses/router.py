import uuid
from typing import Annotated
from database.db_connect.db import get_db
from database.models.courses import Course, CourseStatus
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.courses.schemas import (
    CourseCreate,
    CourseListRead,
    CourseRead,
    CourseStatusUpdate,
    CourseUpdate,
)
from app.api.courses.dependencies import CourseServiceDependency, PipelineServiceDependency
from app.api.jobs.schemas import JobRead
from pipeline.worker import run_job
from services.pipeline_service import PipelineRunError


router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate, service: CourseServiceDependency):
    return await service.create(
        payload.title, brief_json=payload.brief_json, created_by=payload.created_by
    )


@router.get("", response_model=CourseListRead)
async def list_courses(
    service: CourseServiceDependency,
    status_filter: Annotated[CourseStatus | None, Query(alias="status")] = None,
    created_by: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    repo = service.repo
    if status_filter is not None:
        items = await repo.list_by_status(status_filter, limit=limit, offset=offset)
        total = await repo.count(Course.status == status_filter)
    elif created_by is not None:
        items = await repo.list_by_creator(created_by, limit=limit, offset=offset)
        total = await repo.count(Course.created_by == created_by)
    else:
        items = await repo.find_many(limit=limit, offset=offset, order_by=Course.updated_at.desc())
        total = await repo.count()
    return CourseListRead(items=items, total=total, limit=limit, offset=offset)


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(course_id: uuid.UUID, service: CourseServiceDependency):
    course = await service.get(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    return course


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(course_id: uuid.UUID, payload: CourseUpdate, service: CourseServiceDependency):
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустое обновление")
    try:
        return await service.update_fields(course_id, **data)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{course_id}/status", response_model=CourseRead)
async def change_course_status(
    course_id: uuid.UUID, payload: CourseStatusUpdate, service: CourseServiceDependency
):
    try:
        return await service.change_status(course_id, payload.status)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{course_id}/run", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
async def run_course_pipeline(
    course_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    pipeline_service: PipelineServiceDependency,
):
    """Запустить пайплайн генерации курса в фоне.

    Логика — в PipelineService (общий для REST и MCP); здесь только адаптер.
    Ожидается, что в brief_json курса лежит поле raw_brief с текстом брифа.
    """
    try:
        start = await pipeline_service.create_run(course_id)
    except PipelineRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    background_tasks.add_task(run_job, start.job.id, course_id, start.raw_brief)
    return start.job


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: uuid.UUID, service: CourseServiceDependency):
    deleted = await service.delete(course_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
