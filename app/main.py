from fastapi import FastAPI, HTTPException, status

from app.api import (
    course_versions,
    courses,
    events,
    feedback,
    jobs,
    references,
    usage_log,
    users,
)

app = FastAPI(title="TS Hack API", version="0.1.0")

# KeyError из сервисного слоя -> 404, ValueError -> 409/400 обрабатываются локально,
# поэтому тут только глобальный catch-all для непредвиденных ситуаций.


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(courses.router)
app.include_router(course_versions.router)
app.include_router(jobs.router)
app.include_router(events.router)
app.include_router(feedback.router)
app.include_router(references.router)
app.include_router(usage_log.router)
