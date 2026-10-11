"""Тесты эндпоинта POST /courses/{id}/run (Этап 3)."""

import importlib
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.courses.dependencies import get_course_service
from app.api.jobs.dependencies import get_job_service
from app.main import app
from database.models.courses import Course, CourseStatus
from database.models.jobs import Job, JobStatus

# Модуль роутера (import ... as подхватывает атрибут пакета, поэтому importlib)
courses_router_module = importlib.import_module("app.api.courses.router")


class FakeCourseService:
    def __init__(self, course: Course | None) -> None:
        self._course = course

    async def get(self, course_id: uuid.UUID) -> Course | None:
        return self._course


class FakeJobService:
    def __init__(self) -> None:
        self.created: list[Job] = []

    async def create(self, course_id: uuid.UUID) -> Job:
        job = Job(
            id=uuid.uuid4(),
            course_id=course_id,
            status=JobStatus.QUEUED,
            progress=0,
            created_at=datetime.now(timezone.utc),
        )
        self.created.append(job)
        return job


def make_course(brief_json: dict | None = None) -> Course:
    return Course(
        id=uuid.uuid4(),
        title="Курс",
        brief_json=brief_json or {},
        status=CourseStatus.DRAFT,
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_run_404_when_course_missing() -> None:
    app.dependency_overrides[get_course_service] = lambda: FakeCourseService(None)
    app.dependency_overrides[get_job_service] = lambda: FakeJobService()
    client = TestClient(app)

    resp = client.post(f"/courses/{uuid.uuid4()}/run")

    assert resp.status_code == 404


def test_run_400_without_raw_brief() -> None:
    course = make_course(brief_json={})
    app.dependency_overrides[get_course_service] = lambda: FakeCourseService(course)
    app.dependency_overrides[get_job_service] = lambda: FakeJobService()
    client = TestClient(app)

    resp = client.post(f"/courses/{course.id}/run")

    assert resp.status_code == 400
    assert "raw_brief" in resp.json()["detail"]


def test_run_202_creates_job_and_starts_worker(monkeypatch) -> None:
    course = make_course(brief_json={"raw_brief": "Курс по X на 24 часа"})
    job_service = FakeJobService()
    app.dependency_overrides[get_course_service] = lambda: FakeCourseService(course)
    app.dependency_overrides[get_job_service] = lambda: job_service

    calls: list[tuple] = []

    async def fake_run_job(job_id, course_id, raw_brief) -> None:
        calls.append((job_id, course_id, raw_brief))

    monkeypatch.setattr(courses_router_module, "run_job", fake_run_job)
    client = TestClient(app)

    resp = client.post(f"/courses/{course.id}/run")

    assert resp.status_code == 202
    assert len(job_service.created) == 1
    job = job_service.created[0]
    assert resp.json()["id"] == str(job.id)
    assert calls == [(job.id, course.id, "Курс по X на 24 часа")]


def test_run_409_when_job_already_active(monkeypatch) -> None:
    course = make_course(brief_json={"raw_brief": "Курс по X"})
    app.dependency_overrides[get_course_service] = lambda: FakeCourseService(course)

    class BusyJobService(FakeJobService):
        async def create(self, course_id: uuid.UUID) -> Job:
            raise ValueError("Для курса уже есть активная задача")

    app.dependency_overrides[get_job_service] = lambda: BusyJobService()
    client = TestClient(app)

    resp = client.post(f"/courses/{course.id}/run")

    assert resp.status_code == 409