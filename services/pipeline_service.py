"""Сервис запуска пайплайна — общий для REST и MCP (без привязки к FastAPI).

Принцип: вся бизнес-логика живёт здесь; FastAPI-роутер и MCP-сервер — тонкие адаптеры.
"""

import uuid
from dataclasses import dataclass

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.jobs import Job
from services.courses.service import CourseService
from services.jobs.service import JobService


class PipelineRunError(ValueError):
    """Ошибка запуска пайплайна."""

    status_code: int = 400


class CourseNotFoundError(PipelineRunError):
    status_code = 404


class NoBriefError(PipelineRunError):
    status_code = 400


class JobAlreadyActiveError(PipelineRunError):
    status_code = 409


@dataclass
class RunStart:
    """Результат подготовки запуска: джоба + текст брифа для worker'а."""

    job: Job
    raw_brief: str


class PipelineService:
    """Композиция CourseService + JobService для запуска генерации курса."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.courses = CourseService(session)
        self.jobs = JobService(session)

    async def create_run(self, course_id: uuid.UUID) -> RunStart:
        """Подготовить запуск: проверить курс и бриф, создать джобу.

        Возвращает джобу и текст брифа; сам граф запускает вызывающий код (worker).
        """
        course = await self.courses.get(course_id)
        if course is None:
            raise CourseNotFoundError(f"Курс с id={course_id} не найден")
        raw_brief = (course.brief_json or {}).get("raw_brief")
        if not raw_brief:
            raise NoBriefError("В brief_json курса нет поля raw_brief с текстом брифа")
        try:
            job = await self.jobs.create(course_id)
        except ValueError as exc:
            raise JobAlreadyActiveError(str(exc)) from exc
        logger.info("Джоба {} создана для курса {}", job.id, course_id)
        return RunStart(job=job, raw_brief=raw_brief)