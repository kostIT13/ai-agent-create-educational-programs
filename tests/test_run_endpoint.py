"""Тесты эндпоинта POST /courses/{id}/run (Этап 3)."""

import importlib
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.courses.dependencies import get_pipeline_service
from app.main import app
from database.models.jobs import Job, JobStatus
from services.pipeline_service import (
    CourseNotFoundError,
    JobAlreadyActiveError,
    NoBriefError,
    RunStart,
)

# Модуль роутера (import ... as подхватывает атрибут пакета, поэтому importlib)
courses_router_module = importlib.import_module("app.api.courses.router")


class FakePipelineService:
    def __init__(self, result: RunStart | None = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.calls: list[uuid.UUID] = []

    async def create_run(self, course_id: uuid.UUID) -> RunStart:
        self.calls.append(course_id)
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


def make_job(course_id: uuid.UUID) -> Job:
    return Job(
        id=uuid.uuid4(),
        course_id=course_id,
        status=JobStatus.QUEUED,
        progress=0,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_run_404_when_course_missing() -> None:
    app.dependency_overrides[get_pipeline_service] = lambda: FakePipelineService(
        error=CourseNotFoundError("Курс не найден")
    )
    client = TestClient(app)

    resp = client.post(f"/courses/{uuid.uuid4()}/run")

    assert resp.status_code == 404


def test_run_400_without_raw_brief() -> None:
    app.dependency_overrides[get_pipeline_service] = lambda: FakePipelineService(
        error=NoBriefError("В brief_json курса нет поля raw_brief с текстом брифа")
    )
    client = TestClient(app)

    resp = client.post(f"/courses/{uuid.uuid4()}/run")

    assert resp.status_code == 400
    assert "raw_brief" in resp.json()["detail"]


def test_run_202_creates_job_and_starts_worker(monkeypatch) -> None:
    course_id = uuid.uuid4()
    job = make_job(course_id)
    service = FakePipelineService(result=RunStart(job=job, raw_brief="Курс по X на 24 часа"))
    app.dependency_overrides[get_pipeline_service] = lambda: service

    calls: list[tuple] = []

    async def fake_run_job(job_id, course_id_, raw_brief) -> None:
        calls.append((job_id, course_id_, raw_brief))

    monkeypatch.setattr(courses_router_module, "run_job", fake_run_job)
    client = TestClient(app)

    resp = client.post(f"/courses/{course_id}/run")

    assert resp.status_code == 202
    assert service.calls == [course_id]
    assert resp.json()["id"] == str(job.id)
    assert calls == [(job.id, course_id, "Курс по X на 24 часа")]


def test_run_409_when_job_already_active() -> None:
    app.dependency_overrides[get_pipeline_service] = lambda: FakePipelineService(
        error=JobAlreadyActiveError("Для курса уже есть активная задача")
    )
    client = TestClient(app)

    resp = client.post(f"/courses/{uuid.uuid4()}/run")

    assert resp.status_code == 409