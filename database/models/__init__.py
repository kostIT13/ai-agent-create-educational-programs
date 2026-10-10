"""SQLAlchemy-модели таблиц (plan.md §7.2).

Импорт всех моделей здесь нужен для автогенерации миграций Alembic.
"""

from database.models.users import User, UserRole
from database.models.courses import Course, CourseStatus
from database.models.course_versions import CourseVersion
from database.models.jobs import Job, JobStatus
from database.models.events import Event, EventStatus
from database.models.references import Reference
from database.models.feedback import Feedback
from database.models.usage_log import UsageLog

__all__ = [
    "User",
    "UserRole",
    "Course",
    "CourseStatus",
    "CourseVersion",
    "Job",
    "JobStatus",
    "Event",
    "EventStatus",
    "Reference",
    "Feedback",
    "UsageLog",
]
