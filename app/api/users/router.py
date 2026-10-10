"""Эндпоинты пользователей + зависимость-инъекция сервиса."""

import uuid
from typing import Annotated

from database.db_connect.db import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.schemas import UserCreate, UserListRead, UserParams, UserRead, UserUpdate
from services.users.service import UserService


async def get_user_service(session: AsyncSession = Depends(get_db)):
    return UserService(session)


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, service: UserServiceDependency):
    try:
        return await service.create(payload.email, role=payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=UserListRead)
async def list_users(service: UserServiceDependency, params: Annotated[UserParams, Query()]):
    from database.models.users import User

    repo = service.repo
    items = await repo.find_many(limit=params.limit, offset=params.offset)
    total = await repo.count()
    return UserListRead(items=items, total=total, limit=params.limit, offset=params.offset)


@router.get("/by-email", response_model=UserRead)
async def get_user_by_email(email: str, service: UserServiceDependency):
    user = await service.get_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, service: UserServiceDependency):
    user = await service.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: uuid.UUID, payload: UserUpdate, service: UserServiceDependency):
    try:
        return await service.change_role(user_id, payload.role)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, service: UserServiceDependency):
    deleted = await service.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
