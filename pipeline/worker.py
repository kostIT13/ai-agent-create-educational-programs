"""Фоновый worker: прогон пайплайна с записью событий, прогресса и версий курса."""

import uuid
from typing import Any

from loguru import logger
from pydantic import BaseModel

from core.models import CourseGraph
from database.db_connect.db import async_session_maker
from database.models.courses import CourseStatus
from database.models.events import EventStatus
from llm.client import get_llm_client
from pipeline.workflow import build_workflow
from rag.retriever import Retriever
from services.course_versions.service import CourseVersionService
from services.courses.service import CourseService
from services.events.service import EventService
from services.jobs.service import JobService

# Прогресс джобы по завершённым узлам графа
NODE_PROGRESS: dict[str, int] = {
    "intake": 25,
    "competency": 50,
    "curriculum": 75,
    "validate": 100,
}


def _jsonable(value: Any) -> Any:
    """Рекурсивно привести Pydantic-модели к JSON-совместимым структурам."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


async def run_job(job_id: uuid.UUID, course_id: uuid.UUID, raw_brief: str) -> None:
    """Исполнить джобу: граф LangGraph + события узлов + прогресс + версия курса.

    Вызывается из фона (BackgroundTasks). Все ошибки логируются, джоба помечается failed.
    """
    async with async_session_maker() as session:
        jobs = JobService(session)
        events = EventService(session)
        courses = CourseService(session)
        versions = CourseVersionService(session)

        try:
            await jobs.start(job_id)
            await courses.change_status(course_id, CourseStatus.PROCESSING)
            await session.commit()
        except Exception as exc:
            logger.exception("Не удалось запустить джобу {}: {}", job_id, exc)
            await session.rollback()
            return

        llm = get_llm_client()
        # RAG-контекст: если Qdrant недоступен или референсов нет — агенты
        # работают без контекста (Retriever.search вернёт пустой список).
        retriever = Retriever(course_id)
        graph = build_workflow(llm, retriever=retriever)
        state: dict[str, Any] = {"raw_brief": raw_brief}

        try:
            async for update in graph.astream(state, stream_mode="updates"):
                for node_name, node_update in update.items():
                    state.update(node_update)
                    await events.log(
                        job_id,
                        node_name,
                        EventStatus.COMPLETED,
                        payload=_jsonable(node_update),
                    )
                    progress = NODE_PROGRESS.get(node_name)
                    if progress is not None:
                        await jobs.set_progress(job_id, progress)
                    await session.commit()
                    logger.info("Узел {} завершён (job={})", node_name, job_id)

            errors = state.get("errors") or []
            if errors:
                raise RuntimeError("Валидация не пройдена:\n- " + "\n- ".join(errors))

            graph_result = CourseGraph(
                brief=state["brief"],
                competencies=state["competencies"],
                outcomes=state["outcomes"],
                modules=state["modules"],
            )
            graph_json = graph_result.model_dump(mode="json")
            brief_json = {
                "raw_brief": raw_brief,
                "brief": graph_result.brief.model_dump(mode="json"),
            }

            await versions.create_next_version(course_id, graph_json)
            await courses.update_fields(course_id, brief_json=brief_json)
            await courses.change_status(course_id, CourseStatus.READY)
            await jobs.complete(job_id)
            await session.commit()
            logger.info("Джоба {} завершена успешно (курс {})", job_id, course_id)
        except Exception as exc:
            await session.rollback()
            try:
                await jobs.fail(job_id, str(exc))
                await courses.change_status(course_id, CourseStatus.FAILED)
                await session.commit()
            except Exception:
                await session.rollback()
            logger.exception("Джоба {} упала: {}", job_id, exc)