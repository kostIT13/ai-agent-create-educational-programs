# TS Hack — ИИ-агент для создания образовательных программ

Репозиторий для трека хакатона: агент по запросу пользователя проектирует программу обучения
(компетенции, структуру, материалы курса) на основе брифа и референсов.

Ключевая идея — **мультиагентный конвейер вокруг единого графа курса**: `Brief → Competency →
Outcome → Module → артефакты (лекции, семинары, тесты)`. Каждая сущность трассируется до
компетенции и источника (`source_refs`), а все артефакты генерируются из одного графа —
это обеспечивает согласованность и проверяемость.

## Статус (актуальный)

| Этап | Что сделано | Статус |
|---|---|---|
| 0 | docker-compose (postgres + api), дефолты конфигов | ✅ |
| 1 | Pydantic-схемы графа курса ([`core/models/`](core/models/__init__.py:1)) | ✅ |
| 2 | Агенты Intake → Competency → Curriculum + валидаторы + LangGraph-граф | ✅ |
| 3 | `POST /courses/{id}/run` + worker (события, прогресс, версии) + SSE | ✅ |
| 4 | RAG: Docling → Qdrant → `source_refs` | 🚧 в работе |
| 5–11 | Остальные агенты, экспорт, фронт, evals, MCP, MLflow | ⏳ план |

Подробный план: [`workflows/next-steps.md`](workflows/next-steps.md:1), RAG: [`workflows/rag_plan.md`](workflows/rag_plan.md:1).

## Стек

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy (async) · PostgreSQL · LangGraph · LangChain-OpenAI ·
uv · Docker Compose. Evals/Observability: MLflow (план). LLM: свой клиент с structured output + fallback.

## Структура репозитория

```text
agent/            # агенты (Intake, Competency, Curriculum) + промпты в agent/prompts/
pipeline/         # LangGraph: узлы, workflow, runner, worker (фоновый прогон джобы)
validators/       # детерминированные проверки курса (часы, связность, циклы)
core/models/      # Pydantic-схемы графа курса (Brief, Competency, Outcome, Module, ...)
core/configs/     # конфиги (БД, LLM)
llm/              # LLMClient: chat/stream/structured + fallback
rag/              # RAG-контур (реализуется в Этапе 4)
services/         # сервисный слой: Course, Job, Event, CourseVersion, PipelineService
app/api/          # FastAPI-роутеры (тонкие адаптеры поверх сервисов)
database/         # SQLAlchemy async-модели + Alembic-миграции
tests/            # pytest (23 теста)
workflows/        # планы: next-steps, rag_plan, plan, claude-plan, qwen-plan
diagrams/         # Mermaid (.mmd) + тест D2 (.d2)
```

## Быстрый старт

Требования: Docker, uv (или pip).

```bash
# 1. Конфигурация
cp .env.example .env          # вписать LLM_API_KEY

# 2. Запуск стека (postgres + api, миграции применяются автоматически)
docker compose up --build
# API на http://localhost:8000, OpenAPI docs: http://localhost:8000/docs

# 3. Локальные тесты
uv sync
uv run pytest tests/ -v       # 23 passed
```

## API (основные эндпоинты)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | проверка живости |
| `POST` | `/courses` | создать курс: `{title, brief_json: {raw_brief: "..."}}` |
| `GET` | `/courses` | список курсов (фильтры: status, created_by) |
| `GET` | `/courses/{id}` | курс |
| `POST` | `/courses/{id}/run` | запустить пайплайн в фоне → `202` + `job` |
| `GET` | `/jobs/{id}` | статус джобы (progress) |
| `GET` | `/events/job/{id}` | история событий (поллинг) |
| `GET` | `/events/job/{id}/stream` | **SSE-лента** событий узлов (для live-графа) |

**Жизненный цикл генерации:** `POST /courses/{id}/run` → джоба `queued → running → completed`,
курс `draft → processing → ready`; по узлам графа пишутся события и прогресс (25/50/75/100);
результат сохраняется в `course_versions` (graph_json) и читается из `GET /courses/{id}`.

## Принципы

- **Сервисный слой без привязки к FastAPI** — REST, SSE и будущий MCP-сервер — три тонких «входа»
  в одно ядро (`services/pipeline_service.py` и др.).
- **Единый граф курса** — единственный источник правды; артефакты не генерируются «друг из друга».
- **Vалидация до генерации артефактов** — детерминированные проверки (`validators/`) до того,
  как ошибка размножится на весь пакет.
- **Структурированный вывод** — каждый агент возвращает Pydantic-схему (валидация + ретраи).

## Документация

- [`workflows/plan.md`](workflows/plan.md:1) — полная prod-ready концепция (архитектура, RAG, API, демо).
- [`workflows/next-steps.md`](workflows/next-steps.md:1) — рабочий план по этапам (актуальный статус).
- [`workflows/rag_plan.md`](workflows/rag_plan.md:1) — подробный план RAG-контура.
- [`diagrams/`](diagrams/README.md:1) — архитектура, пайплайн, RAG, БД, MCP, MLflow (Mermaid + D2).