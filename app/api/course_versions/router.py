import uuid
from typing import Annotated
from database.db_connect.db import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.course_versions.schemas import CourseVersionCreate, CourseVersionRead
from services.course_versions.service import CourseVersionService
from app.api.course_versions.dependencies import CourseVersionServiceDependency


router = APIRouter(prefix="/course-versions", tags=["course-versions"])


@router.post("", response_model=CourseVersionRead, status_code=status.HTTP_201_CREATED)
async def create_course_version(
    payload: CourseVersionCreate, service: CourseVersionServiceDependency
):
    """Создать следующую версию графа курса (номер вычисляется автоматически)."""
    return await service.create_next_version(
        payload.course_id, payload.graph_json, diff_json=payload.diff_json
    )


@router.get("/{version_id}", response_model=CourseVersionRead)
async def get_course_version(version_id: uuid.UUID, service: CourseVersionServiceDependency):
    obj = await service.get(version_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Версия не найдена")
    return obj


@router.get("/course/{course_id}", response_model=list[CourseVersionRead])
async def list_course_versions(course_id: uuid.UUID, service: CourseVersionServiceDependency):
    return await service.list_by_course(course_id)


@router.get("/course/{course_id}/latest", response_model=CourseVersionRead)
async def get_latest_course_version(
    course_id: uuid.UUID, service: CourseVersionServiceDependency
):
    obj = await service.get_latest(course_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Версии не найдены")
    return obj


@router.get("/course/{course_id}/number/{version}", response_model=CourseVersionRead)
async def get_course_version_by_number(
    course_id: uuid.UUID, version: int, service: CourseVersionServiceDependency
):
    obj = await service.get_by_number(course_id, version)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Версия не найдена")
    return obj
