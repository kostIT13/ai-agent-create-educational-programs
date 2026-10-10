import uuid
from abc import abstractmethod

from database.models.users import User
from services.base import AbstractRepository


class AbstractUserRepository(AbstractRepository[User]):

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError
