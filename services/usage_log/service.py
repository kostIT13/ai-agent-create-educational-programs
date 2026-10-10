import uuid
from datetime import datetime
from decimal import Decimal
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.usage_log import UsageLog
from services.usage_log.base import AbstractUsageLogRepository
from services.usage_log.repository import UsageLogRepository


class UsageLogService:
    def __init__(
        self,
        session: AsyncSession,
        repo: AbstractUsageLogRepository | None = None,
    ) -> None:
        self.session = session
        self.repo: AbstractUsageLogRepository = repo or UsageLogRepository(session)

    async def log_request(
        self,
        course_id: uuid.UUID,
        model: str,
        *,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost: Decimal = Decimal("0"),
    ) -> UsageLog:
        """Зафиксировать один вызов LLM."""
        entry = await self.repo.create(
            course_id=course_id,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
        )
        logger.debug(
            "LLM usage: course={} model={} in={} out={} cost={}",
            course_id,
            model,
            tokens_in,
            tokens_out,
            cost,
        )
        return entry

    async def list_by_course(self, course_id: uuid.UUID) -> list[UsageLog]:
        return await self.repo.list_by_course(course_id)

    async def totals(
        self, *, since: datetime | None = None, until: datetime | None = None
    ) -> dict[str, Decimal | int]:
        """Суммарные токены/стоимость/число запросов за период."""
        return await self.repo.totals(since=since, until=until)

    async def totals_by_model(
        self, *, since: datetime | None = None, until: datetime | None = None
    ) -> list[tuple[str, int, int, Decimal]]:
        """Разбивка расхода по моделям за период."""
        return await self.repo.totals_by_model(since=since, until=until)
