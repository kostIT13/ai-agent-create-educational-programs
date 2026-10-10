import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, select
from database.models.usage_log import UsageLog
from services.repository import SQLAlchemyRepository
from services.usage_log.base import AbstractUsageLogRepository


class UsageLogRepository(AbstractUsageLogRepository, SQLAlchemyRepository[UsageLog]):
    model = UsageLog

    async def list_by_course(
        self, course_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[UsageLog]:
        return await self.find_many(
            UsageLog.course_id == course_id,
            limit=limit,
            offset=offset,
            order_by=UsageLog.ts.desc(),
        )

    async def totals(
        self, *, since: datetime | None = None, until: datetime | None = None
    ) -> dict[str, Decimal | int]:
        conditions = []
        if since is not None:
            conditions.append(UsageLog.ts >= since)
        if until is not None:
            conditions.append(UsageLog.ts <= until)

        stmt = select(
            func.coalesce(func.sum(UsageLog.tokens_in), 0),
            func.coalesce(func.sum(UsageLog.tokens_out), 0),
            func.coalesce(func.sum(UsageLog.cost), Decimal(0)),
            func.count(),
        )
        if conditions:
            stmt = stmt.where(*conditions)
        row = (await self.session.execute(stmt)).one()
        return {
            "tokens_in": int(row[0]),
            "tokens_out": int(row[1]),
            "cost": Decimal(row[2]),
            "requests": int(row[3]),
        }

    async def totals_by_model(
        self, *, since: datetime | None = None, until: datetime | None = None
    ) -> list[tuple[str, int, int, Decimal]]:
        conditions = []
        if since is not None:
            conditions.append(UsageLog.ts >= since)
        if until is not None:
            conditions.append(UsageLog.ts <= until)

        stmt = select(
            UsageLog.model,
            func.coalesce(func.sum(UsageLog.tokens_in), 0),
            func.coalesce(func.sum(UsageLog.tokens_out), 0),
            func.coalesce(func.sum(UsageLog.cost), Decimal(0)),
        ).group_by(UsageLog.model)
        if conditions:
            stmt = stmt.where(*conditions)

        result = await self.session.execute(stmt)
        return [
            (row[0], int(row[1]), int(row[2]), Decimal(row[3]))
            for row in result.all()
        ]
