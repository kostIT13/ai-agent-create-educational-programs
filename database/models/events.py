import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db_connect.base import Base


class EventStatus(str, enum.Enum):

    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"  


class Event(Base):

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_job_id_ts", "job_id", "ts"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
    )
    node: Mapped[str] = mapped_column(String(128)) 
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status"),
        default=EventStatus.STARTED,
        server_default=EventStatus.STARTED.value,
    )
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    job = relationship("Job", back_populates="events")

    def __repr__(self) -> str:  
        return f"<Event job_id={self.job_id} node={self.node!r} status={self.status}>"
