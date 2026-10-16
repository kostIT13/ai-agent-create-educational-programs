# TS Hack — ИИ-агент для создания образовательных программ АЦР

Репозиторий для трека хакатона: агент по запросу методиста проектирует программу обучения АЦР
(шаблон, компетенции, структуру, материалы курса) на основе брифа и референсов и собирает
полный комплект: программа .docx по шаблону АЦР, слайды .pptx, тесты в LMS-формате, JSON.

**Кейс:** заказчик — Академия цифрового развития (Магас), кейсодатель — GigaCowork (Сбер).
**Два шаблона АЦР:** №1 ДПП ПК/стажировка (273-ФЗ + приказ Минобрнауки № 499, профстандарты,
ЛК/ПР/ЛБ/СРС/ИА), №2 общеразвивающая (приказ Минпросвещения № 629, знания/умения/навыки,
лекции/практика/СР/ИА). Примеры и ТЗ — в [`dataset/`](dataset/main_task.txt:1).

Ключевая идея — **пайплайн навыков вокруг единого графа курса** (как на GigaCowork):
`Intake → TemplateSelector → Competency → Outcome → Module → артефакты (лекции, семинары, тесты) → Critic`.
Каждая сущность трассируется до компетенции и источника (`source_refs`), а все артефакты
генерируются из одного графа — это обеспечивает согласованность, проверку сумм часов и
достоверность (без выдуманных приказов/профстандартов).

## Статус (актуальный)

| Этап | Что сделано | Статус |
|---|---|---|
| 0 | docker-compose (postgres + api), дефолты конфигов | ✅ |
| 1 | Pydantic-схемы графа курса ([`core/models/`](core/models/__init__.py:1)) | ✅ |
| 2 | Агенты Intake → Competency → Curriculum + валидаторы + LangGraph-граф | ✅ |
| 3 | `POST /courses/{id}/run` + worker (события, прогресс, версии) + SSE | ✅ |
| 4 | RAG: Docling → Qdrant → `source_refs` | 🚧 в работе |
| 5 | **TemplateSelector (2 шаблона АЦР)**, чекпоинты утверждения, Assessment/Seminar/Lecture/Critic | ⏳ план |
| 6 | Экспорт: **DOCX по шаблонам АЦР**, PPTX, LMS (GIFT/XML/CSV), JSON/ZIP | ⏳ план |
| 7–11 | Фронт, evals по чек-листам ТЗ, MCP, MLflow, prod-практики | ⏳ план |

Подробный план: [`workflows/plan.md`](workflows/plan.md:1) (актуализирован под данные хакатона),
этапы: [`workflows/next-steps.md`](workflows/next-steps.md:1), RAG: [`workflows/rag_plan.md`](workflows/rag_plan.md:1).

## Стек

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy (async) · PostgreSQL · LangGraph · Qdrant · Docling ·
uv · Docker Compose. **LLM: свой OpenAI-совместимый клиент с structured output + fallback** —
сейчас на текущем dev-провайдере; по ТЗ целевой провайдер — **Cloud.ru EFM
(GigaChat / Qwen / DeepSeek)**, подключим, когда выдадут доступы (смена `BASE_URL`/моделей в `.env`).
Evals/Observability: MLflow (план).

## Структура репозитория

```text
agent/            # навыки (Intake, Competency, Curriculum + TemplateSelector) + промпты
pipeline/         # LangGraph: узлы, workflow, runner, worker (фоновый прогон джобы)
validators/       # детерминированные проверки курса (часы, связность, циклы)
core/models/      # Pydantic-схемы графа курса (Brief, Template, Competency, Module, ...)
core/configs/     # конфиги (БД, LLM - Cloud.ru)
llm/              # LLMClient: chat/stream/structured + fallback внутри каталога Cloud.ru
rag/              # RAG-контур (Docling -> Qdrant -> source_refs)
services/         # сервисный слой: Course, Job, Event, Version, PipelineService, Reference, Usage
app/api/          # FastAPI-роутеры (тонкие адаптеры поверх сервисов)
database/         # SQLAlchemy async-модели + Alembic-миграции
exporters/        # (план) DOCX по 2 шаблонам АЦР, PPTX, LMS GIFT/XML/CSV, JSON/ZIP
dataset/          # ТЗ хакатона + 2 примера программ АЦР (эталоны шаблонов)
tests/            # pytest
workflows/        # планы: plan (v2 - данные хакатона), next-steps, rag_plan
diagrams/         # Mermaid (.mmd) + тест D2 (.d2)
```

## Быстрый старт

Требования: Docker, uv (или pip).

```bash
# 1. Конфигурация
cp .env.example .env          # вписать LLM_API_KEY для Cloud.ru EFM +
                              # LLM_BASE_URL (GigaChat/Qwen/DeepSeek), при необходимости RAG_* / QDRANT_URL

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