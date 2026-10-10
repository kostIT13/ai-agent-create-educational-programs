import uuid
from typing import Any, Generic, TypeVar
from sqlalchemy import ColumnExpressionArgument, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_connect.base import Base
from services.base import AbstractRepository

ModelT = TypeVar("ModelT", bound=Base)


class SQLAlchemyRepository(AbstractRepository[ModelT], Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: uuid.UUID) -> Base | None:
        return await self.session.get(self.model, id_)

    async def find_one(self, *conditions: ColumnExpressionArgument[bool]) -> Base | None:
        stmt = select(self.model).where(*conditions).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_many(
        self,
        *conditions: ColumnExpressionArgument[bool],
        limit: int = 100,
        offset: int = 0,
        order_by: ColumnExpressionArgument[Any] | None = None,
    ) -> list[Base]:
        stmt = select(self.model).where(*conditions).limit(limit).offset(offset)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *conditions: ColumnExpressionArgument[bool]) -> int:
        stmt = select(func.count()).select_from(self.model)
        if conditions:
            stmt = stmt.where(*conditions)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, **data: Any) -> Base:
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: Base, **data: Any) -> Base:
        for field, value in data.items():
            setattr(obj, field, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: Base) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def delete_by_id(self, id_: uuid.UUID) -> bool:
        obj = await self.get(id_)
        if obj is None:
            return False
        await self.delete(obj)
        return True
