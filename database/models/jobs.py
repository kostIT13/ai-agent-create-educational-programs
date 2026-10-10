import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Index, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db_connect.base import Base


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):

    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_course_id", "course_id"),
        Index("ix_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"),
        default=JobStatus.QUEUED,
        server_default=JobStatus.QUEUED.value,
    )
    progress: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course = relationship("Course", back_populates="jobs")
    events = relationship(
        "Event",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="Event.ts",
    )

    def __repr__(self) -> str:  
        return f"<Job id={self.id} course_id={self.course_id} status={self.status}>"
