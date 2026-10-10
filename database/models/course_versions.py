import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db_connect.base import Base


class CourseVersion(Base):
    __tablename__ = "course_versions"
    __table_args__ = (
        UniqueConstraint("course_id", "version", name="uq_course_versions_course_version"),
        Index("ix_course_versions_course_id", "course_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
    )
    version: Mapped[int]
    graph_json: Mapped[dict] = mapped_column(JSONB)
    diff_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course = relationship("Course", back_populates="versions")

    def __repr__(self) -> str:  
        return f"<CourseVersion course_id={self.course_id} version={self.version}>"
