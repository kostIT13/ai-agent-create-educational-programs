from database.models.users import User
from services.repository import SQLAlchemyRepository
from services.users.base import AbstractUserRepository


class UserRepository(AbstractUserRepository, SQLAlchemyRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        return await self.find_one(User.email == email)
