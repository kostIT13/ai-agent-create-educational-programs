import uuid
from typing import Annotated
from database.db_connect.db import get_db
from database.models.jobs import JobStatus
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.jobs.schemas import JobCreate, JobFail, JobProgressUpdate, JobRead
from app.api.jobs.dependencies import JobServiceDependency


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, service: JobServiceDependency):
    try:
        return await service.create(payload.course_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: uuid.UUID, service: JobServiceDependency):
    job = await service.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Джоб не найден")
    return job


@router.get("/course/{course_id}", response_model=list[JobRead])
async def list_jobs_by_course(
    course_id: uuid.UUID,
    service: JobServiceDependency,
    status_filter: Annotated[JobStatus | None, Query(alias="status")] = None,
):
    if status_filter is not None:
        jobs = await service.list_by_status(status_filter)
        return [j for j in jobs if j.course_id == course_id]
    return await service.list_by_course(course_id)


@router.post("/{job_id}/start", response_model=JobRead)
async def start_job(job_id: uuid.UUID, service: JobServiceDependency):
    try:
        return await service.start(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{job_id}/progress", response_model=JobRead)
async def set_job_progress(
    job_id: uuid.UUID, payload: JobProgressUpdate, service: JobServiceDependency
):
    job = await service.set_progress(job_id, payload.progress)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Джоб не найден")
    return job


@router.post("/{job_id}/complete", response_model=JobRead)
async def complete_job(job_id: uuid.UUID, service: JobServiceDependency):
    try:
        return await service.complete(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/fail", response_model=JobRead)
async def fail_job(job_id: uuid.UUID, payload: JobFail, service: JobServiceDependency):
    try:
        return await service.fail(job_id, payload.error)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: uuid.UUID, service: JobServiceDependency):
    deleted = await service.delete(job_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Джоб не найден")


@router.post("/{job_id}/cancel", response_model=JobRead)
async def cancel_job(job_id: uuid.UUID, service: JobServiceDependency):
    try:
        return await service.cancel(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
