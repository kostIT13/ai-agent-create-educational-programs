import uuid
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.users import User, UserRole
from services.users.base import AbstractUserRepository
from services.users.repository import UserRepository


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        repo: AbstractUserRepository | None = None,
    ) -> None:
        self.session = session
        self.repo: AbstractUserRepository = repo or UserRepository(session)

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.repo.get(user_id)

    async def get_or_raise(self, user_id: uuid.UUID) -> User:
        user = await self.repo.get(user_id)
        if user is None:
            raise KeyError(f"Пользователь с id={user_id} не найден")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email)

    async def create(self, email: str, role: UserRole = UserRole.VIEWER) -> User:
        """Создать пользователя; email уникален."""
        if await self.repo.get_by_email(email):
            raise ValueError(f"Пользователь с email={email!r} уже существует")
        user = await self.repo.create(email=email, role=role)
        logger.info("Пользователь создан: id={} email={} role={}", user.id, user.email, user.role)
        return user

    async def change_role(self, user_id: uuid.UUID, role: UserRole) -> User:
        user = await self.get_or_raise(user_id)
        return await self.repo.update(user, role=role)

    async def delete(self, user_id: uuid.UUID) -> bool:
        return await self.repo.delete_by_id(user_id)
