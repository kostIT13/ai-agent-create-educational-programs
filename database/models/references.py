import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db_connect.base import Base


class Reference(Base):
    
    __tablename__ = "references"
    __table_args__ = (
        Index("ix_references_course_id", "course_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(512))
    mime: Mapped[str | None] = mapped_column(String(128), nullable=True)
    s3_key: Mapped[str] = mapped_column(String(1024))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course = relationship("Course", back_populates="references")

    def __repr__(self) -> str: 
        return f"<Reference id={self.id} name={self.name!r} s3_key={self.s3_key!r}>"
