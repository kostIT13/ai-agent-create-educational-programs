"""Эндпоинты справочников + зависимость-инъекция сервиса."""

import uuid
from typing import Annotated

from database.db_connect.db import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.references.schemas import ReferenceCreate, ReferenceRead
from services.references.service import ReferenceService


async def get_reference_service(session: AsyncSession = Depends(get_db)):
    return ReferenceService(session)


ReferenceServiceDependency = Annotated[ReferenceService, Depends(get_reference_service)]

router = APIRouter(prefix="/references", tags=["references"])


@router.post("", response_model=ReferenceRead, status_code=status.HTTP_201_CREATED)
async def create_reference(payload: ReferenceCreate, service: ReferenceServiceDependency):
    try:
        return await service.add(
            payload.course_id, payload.name, payload.s3_key, mime=payload.mime
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{reference_id}", response_model=ReferenceRead)
async def get_reference(reference_id: uuid.UUID, service: ReferenceServiceDependency):
    obj = await service.get(reference_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Справочник не найден")
    return obj


@router.get("/course/{course_id}", response_model=list[ReferenceRead])
async def list_course_references(course_id: uuid.UUID, service: ReferenceServiceDependency):
    return await service.list_by_course(course_id)


@router.delete("/{reference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reference(reference_id: uuid.UUID, service: ReferenceServiceDependency):
    deleted = await service.delete(reference_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Справочник не найден")
