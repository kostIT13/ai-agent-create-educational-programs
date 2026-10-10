import uuid
from abc import abstractmethod
from datetime import datetime
from decimal import Decimal
from database.models.usage_log import UsageLog
from services.base import AbstractRepository


class AbstractUsageLogRepository(AbstractRepository[UsageLog]):

    @abstractmethod
    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[UsageLog]:
        raise NotImplementedError

    @abstractmethod
    async def totals(
        self, *, since: datetime | None = None, until: datetime | None = None
    ) -> dict[str, Decimal | int]:
        """Суммарные токены и стоимость за период."""
        raise NotImplementedError

    @abstractmethod
    async def totals_by_model(
        self, *, since: datetime | None = None, until: datetime | None = None
    ) -> list[tuple[str, int, int, Decimal]]:
        """Агрегат по моделям: [(model, tokens_in, tokens_out, cost), ...]."""
        raise NotImplementedError
