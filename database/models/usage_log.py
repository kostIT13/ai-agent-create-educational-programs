import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db_connect.base import Base


class UsageLog(Base):

    __tablename__ = "usage_log"
    __table_args__ = (
        Index("ix_usage_log_course_id_ts", "course_id", "ts"),
        Index("ix_usage_log_model", "model"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
    )
    model: Mapped[str] = mapped_column(String(128))
    tokens_in: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tokens_out: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal("0"), server_default="0"
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course = relationship("Course", back_populates="usage_logs")

    def __repr__(self) -> str: 
        return f"<UsageLog model={self.model!r} tokens_in={self.tokens_in} tokens_out={self.tokens_out}>"
