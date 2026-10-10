import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db_connect.base import Base


class Feedback(Base):

    __tablename__ = "feedback"
    __table_args__ = (
        Index("ix_feedback_course_id", "course_id"),
        Index("ix_feedback_entity_id", "entity_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
    )
    entity_id: Mapped[str] = mapped_column(String(64)) 
    rating: Mapped[int] = mapped_column(SmallInteger) 
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    course = relationship("Course", back_populates="feedback")
    author = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Feedback entity_id={self.entity_id!r} rating={self.rating}>"
