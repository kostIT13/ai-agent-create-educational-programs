"""Pydantic-схемы для эндпоинтов пользователей."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from database.models.users import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    role: UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    created_at: datetime


class UserListRead(BaseModel):
    items: list[UserRead]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(from_attributes=True)


class UserParams(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
