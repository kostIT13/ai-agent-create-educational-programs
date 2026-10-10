import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from sqlalchemy import ColumnExpressionArgument
from database.db_connect.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class AbstractRepository(ABC, Generic[ModelT]):
    """Контракт репозитория: типовые операции над одной моделью."""

    @abstractmethod
    async def get(self, id_: uuid.UUID) -> ModelT | None:
        raise NotImplementedError

    @abstractmethod
    async def find_one(self, *conditions: ColumnExpressionArgument[bool]) -> ModelT | None:
        raise NotImplementedError

    @abstractmethod
    async def find_many(
        self,
        *conditions: ColumnExpressionArgument[bool],
        limit: int = 100,
        offset: int = 0,
        order_by: ColumnExpressionArgument[Any] | None = None,
    ) -> list[ModelT]:
        raise NotImplementedError

    @abstractmethod
    async def count(self, *conditions: ColumnExpressionArgument[bool]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def create(self, **data: Any) -> ModelT:
        raise NotImplementedError

    @abstractmethod
    async def update(self, obj: ModelT, **data: Any) -> ModelT:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, obj: ModelT) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, id_: uuid.UUID) -> bool:
        raise NotImplementedError
