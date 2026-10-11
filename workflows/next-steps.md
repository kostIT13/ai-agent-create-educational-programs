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

## Этап 1. Ядро: Pydantic-схемы графа курса

**Цель:** единый источник правды — структурированный JSON-граф курса (по §7.1 [`plan.md`](plan.md)).

Новый пакет `core/models/` (или `app/schemas/course_graph.py`):

| Файл | Содержимое |
|---|---|
| `brief.py` | `Brief`: тема, цель, аудитория, объём (часы), язык, требования, референсы |
| `competency.py` | `Competency` (id, name, level), `Outcome` (id, competency_id, bloom, text, source_refs) |
| `module.py` | `Module` (id, title, hours{lec,sem,self}, outcomes, prereq) |
| `assessment.py` | `Question` (id, module_id, outcome_id, qtype, prompt, options, correct, difficulty, explanation, source_refs) |
| `seminar.py` | `Seminar` (id, module_id, tasks, rubric) |
| `lecture.py` | `Lecture` (id, module_id, outline, timing, speaker_notes) |
| `course.py` | `CourseGraph` (competencies, outcomes, modules, questions, seminars, lectures) + `CourseState` (TypedDict для LangGraph) |

**Критерий готовности:** схемы валидируются на мок-примере; `CourseGraph` сериализуется в JSON и обратно.

---

## Этап 2. Первый вертикальный срез: Intake → Competency → Curriculum

**Цель:** «бриф → структура курса» через LangGraph с LLM-клиентом (без RAG).

1. Добавить зависимости: `langgraph`, `instructor` (structured output), `tenacity` (retry).
2. `core/graph/state.py` — `CourseState` (TypedDict): brief, competencies, outcomes, modules, critic_report.
3. `core/agents/` — промпты + узлы:
   - `intake.py` — парсинг сырого брифа в `Brief` (structured output, 1 ретрай при невалидном JSON);
   - `competency.py` — `Competency` + `Outcome` (глаголы Блума);
   - `curriculum.py` — `Module` (часы, пререквизиты, привязка к outcomes).
4. `core/graph/workflow.py` — граф `intake → competency → curriculum` + валидаторы:
   - сумма часов == объёму брифа;
   - каждый outcome привязан к компетенции; каждый модуль — к outcomes;
   - нет циклов в пререквизитах.
5. `core/validators/` — детерминированные проверки (переиспользуются Critic'ом позже).

**Критерий готовности:** скрипт/тест прогоняет бриф «Промпт-инжиниринг для PM, 24 ч» → валидный `CourseGraph` с компетенциями и модулями.

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

1. `assessment.py` — вопросы (MCQ, верно/неверно, соответствие, open) с дистракторами и пояснениями.
2. `seminar.py` — задания, рубрики, эталонные решения.
3. `lecture.py` — план лекции: тайминг, тезисы, примеры, заметки лектора.
4. `visual.py` — JSON-структуры слайдов + Mermaid-схемы.
5. `critic.py` — детерминированные проверки (из Этапа 2) + LLM-judge; до 2 итераций доработки.
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

1. **Этап 0**: проверить `docker compose up --build`, добавить `logs/` в `.gitignore`.
2. **Этап 1**: схемы графа курса (фундамент — без него ничего дальше).
3. **Этап 2**: Intake → Competency → Curriculum на LangGraph.
4. **Этап 3**: `POST /run` + worker + SSE.
5. Далее по списку.