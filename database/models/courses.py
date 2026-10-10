import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db_connect.base import Base


class CourseStatus(str, enum.Enum):

    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class Course(Base):
    """Курс: бриф + статус + указатель на текущую версию графа."""

    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(String(512))
    brief_json: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    status: Mapped[CourseStatus] = mapped_column(
        Enum(
            CourseStatus,
            name="course_status",
            values_callable=lambda e: [m.value for m in e],  # храним значения, а не имена
        ),
        default=CourseStatus.DRAFT,
        server_default=CourseStatus.DRAFT.value,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    creator = relationship("User", back_populates="courses", foreign_keys=[created_by])
    versions = relationship(
        "CourseVersion",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseVersion.created_at",
    )
    jobs = relationship(
        "Job",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Job.created_at",
    )
    references = relationship(
        "Reference",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    feedback = relationship(
        "Feedback",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    usage_logs = relationship(
        "UsageLog",
        back_populates="course",
        cascade="all, delete-orphan",
    )


Index("ix_courses_created_by", Course.created_by)
Index("ix_courses_status", Course.status)
