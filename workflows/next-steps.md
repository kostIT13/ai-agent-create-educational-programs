# План работ: вертикальный срез → полный пайплайн

> Статус: актуальный рабочий план (обновляется по мере выполнения).
> Стратегия: **вертикальный срез вместо ширины** — сначала «бриф → структура курса» насквозь,
> затем наращиваем агентов, RAG, экспорт и фронт.

---

## Этап 0. Инфраструктура (сделано)

- [x] Контейнер `api` (FastAPI) в [`docker-compose.yml`](../docker-compose.yml): build из Dockerfile,
      `depends_on: postgres (healthy)`, проброс порта 8000, env из `.env`, авто-миграции
      (`alembic upgrade head` перед стартом uvicorn).
- [x] Исправлена опечатка `DEBAG` → `DEBUG` в [`.env.example`](../.env.example).
- [ ] Проверить запуск: `docker compose up --build` → `GET /health` → `GET /docs`.
- [ ] Добавить `logs/` в `.gitignore` (лог-файлы не должны попадать в git).

---

## Этап 1. Ядро: Pydantic-схемы графа курса (сделано)

**Цель:** единый источник правды — структурированный JSON-граф курса (по §7.1 [`plan.md`](plan.md)).

- [x] `core/models/brief.py` — `Brief` (тема, цель, аудитория, объём, язык, требования,
      ограничения, референсы) + `Hours` (lec/sem/self, `total`).
- [x] `core/models/competency.py` — `BloomLevel` (6 уровней), `Competency`, `Outcome`.
- [x] `core/models/module.py` — `Module` (hours, outcomes, prereq).
- [x] `core/models/assessment.py` — `QuestionType`, `Question` (difficulty 0..1).
- [x] `core/models/seminar.py` — `Task`, `Seminar` (rubric).
- [x] `core/models/lecture.py` — `SlideBlock`, `TimingStep`, `Lecture`.
- [x] `core/models/course.py` — `CourseGraph` (с хелперами), `CriticIssue`/`CriticReport`,
      `CourseState` (TypedDict для LangGraph).
- [x] Тесты [`tests/test_course_graph.py`](../tests/test_course_graph.py) — 7 шт., JSON round-trip.
- [x] dev-группа `pytest`/`pytest-asyncio`, `uv.lock` обновлён.

---

## Этап 2. Первый вертикальный срез: Intake → Competency → Curriculum (сделано)

**Цель:** «бриф → структура курса» через LangGraph с LLM-клиентом (без RAG).

> Структура: всё, что связано с агентами и пайплайном — в корне (`agent/`, `pipeline/`,
> `validators/`), не в `core/`. В `core/` только модели, конфиги, логгер.

- [x] Зависимость `langgraph` добавлена; structured output — через `LLMClient.structured()` с fallback.
- [x] `llm/client.py` — метод `structured(schema)` (with_structured_output + fallback), фикс `chat(model=...)`.
- [x] `agent/base.py` — `generate_structured()`; промпты в `agent/prompts/` (версионируются).
- [x] `agent/intake.py` — сырой бриф → `Brief`.
- [x] `agent/competency.py` — `Competency` + `Outcome` (глаголы Блума).
- [x] `agent/curriculum.py` — `Module` (часы, пререквизиты, привязка к outcomes).
- [x] `validators/course.py` — детерминированные проверки: сумма часов, связность
      outcomes/компетенций, отсутствие циклов в пререквизитах.
- [x] `pipeline/workflow.py` — граф `intake → competency → curriculum → validate`;
      `pipeline/runner.py` — `run_pipeline()` → `CourseGraph` или `PipelineError`.
- [x] Offline-тесты (фейковый LLM): [`tests/test_pipeline_offline.py`](../tests/test_pipeline_offline.py),
      [`tests/test_validators.py`](../tests/test_validators.py) — 19 тестов суммарно.

**Критерий готовности:** offline-прогон брифа → валидный `CourseGraph`; реальный прогон — на машине
с настроенным `LLM_API_KEY` (команда `uv run python -c "..."` / следующий этап).

---

## Этап 3. Запуск пайплайна через API + worker

**Цель:** джоба реально исполняет граф, пишет события и прогресс.

1. `POST /api/v1/courses/{id}/run` — создаёт джобу (если нет активной) и запускает граф в фоне
   (`BackgroundTasks` или отдельный worker-процесс).
2. Worker: `job.start()` → прогон графа → на каждом узле пишет `Event` (node, status, payload)
   и обновляет `progress` → `job.complete()` / `job.fail()`; курс → `ready` / `failed`.
3. Результат графа сохраняется в `course_versions` (graph_json) + `courses.brief_json`.
4. `GET /api/v1/courses/{id}/events` (SSE) — стрим событий для фронта (сейчас есть только поллинг).

**Критерий готовности:** `POST /run` → SSE-лента с событиями узлов → курс в статусе `ready` с графом в БД.

---

## Этап 4. RAG-контур (референсы)

**Цель:** агенты учитывают референсы и возвращают `source_refs` (по §8 [`plan.md`](plan.md)).

1. `rag/ingest.py` — Docling (PDF/DOCX/PPTX → markdown) + чанкинг по структуре.
2. `rag/embeddings.py` — bge-m3 (dense + sparse) локально, fallback `text-embedding-3-large`.
3. `rag/store.py` — Qdrant: коллекция `course_{id}_refs`, hybrid search (dense + sparse, RRF) + rerank
   (bge-reranker-v2-m3, top-30 → top-6).
4. `rag/retriever.py` — обёртка «чанки → `<source id>` в промпте» (анти-prompt-injection).
5. Подключить к агентам: Competency/Curriculum берут требования из референсов; `source_refs` в моделях.
6. `POST /api/v1/courses/{id}/refs` — загрузка файлов/URL → ingest.

**Критерий готовности:** загрузка PDF → агенты цитируют чанки (`source_refs` непустые).

---

## Этап 5. Остальные агенты (параллельно по модулям)

**Цель:** полный пакет курса (по §5 [`plan.md`](plan.md)).

1. `agent/assessment.py` — вопросы (MCQ, верно/неверно, соответствие, open) с дистракторами и пояснениями.
2. `agent/seminar.py` — задания, рубрики, эталонные решения.
3. `agent/lecture.py` — план лекции: тайминг, тезисы, примеры, заметки лектора.
4. `agent/visual.py` — JSON-структуры слайдов + Mermaid-схемы.
5. `agent/critic.py` — детерминированные проверки (из Этапа 2) + LLM-judge; до 2 итераций доработки.
6. Параллелизм по модулям через `Send` API LangGraph.

**Критерий готовности:** полный прогон брифа → `CourseGraph` со всеми артефактами + отчёт Critic.

---

## Этап 6. Экспорт

**Цель:** ZIP / PPTX / DOCX / Moodle XML (по §11 [`plan.md`](plan.md)).

1. `core/exporters/pptx.py` — python-pptx: слайды из JSON-структур (1 качественный шаблон).
2. `core/exporters/docx.py` — python-docx: рабочая программа, методичка.
3. `core/exporters/moodle.py` — Moodle XML / GIFT из банка вопросов.
4. `core/exporters/zip.py` — сборка пакета + `course.json`.
5. `GET /api/v1/courses/{id}/export?fmt=zip|pptx|docx|moodle`.

**Критерий готовности:** из готового курса скачивается ZIP с реальными PPTX/DOCX/Moodle XML.

---

## Этап 7. Frontend (можно параллельно с Этапом 3–5, на моках)

**Цель:** 4 P0-экрана (по §10 [`plan.md`](plan.md)): бриф, live-пайплайн (React Flow + SSE),
чекпоинт компетенций, граф курса + heatmap.

1. `apps/web` — Vite + React 18 + TS + Tailwind + shadcn/ui.
2. Мок-данные, совпадающие с Pydantic-схемами (Этап 1) — фронт не ждёт бэкенд.
3. `openapi-typescript` — TS-типы из OpenAPI FastAPI.
4. Подключение реального API: SSE-лента, чекпоинты, экспорт.

**Критерий готовности:** бриф → живой граф агентов → редактируемые компетенции → граф курса.

---

## Этап 8. Качество и демо

1. Evals: 3 эталонных брифа + рубрики LLM-judge (`eval/`).
2. Тесты: `pytest` на валидаторы, сервисы, API (smoke).
3. Langfuse-трейсы на LLM-вызовы (опционально, если хватит времени).
4. Демо: предгенерированный курс в БД + скрипт на 4–5 минут (по §17 [`plan.md`](plan.md)).

---

## Порядок выполнения (ближайшие шаги)

1. **Этап 2 ✓** — вертикальный срез «бриф → структура курса» готов (агенты + валидаторы + граф + тесты).
2. **Этап 3** — `POST /run` + worker + SSE: связать пайплайн с API и БД.
3. Далее по списку.