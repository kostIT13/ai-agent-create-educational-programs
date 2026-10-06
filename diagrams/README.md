# Диаграммы проекта

Набор Mermaid-диаграмм для ИИ-агента создания образовательных программ.
Все файлы — исходники в формате Mermaid (`.mmd`).

## Список диаграмм

| Файл | Что показывает |
|---|---|
| [`architecture.mmd`](architecture.mmd) | High-level архитектура: frontend, backend, LangGraph, LLM-роутер, БД |
| [`pipeline.mmd`](pipeline.mmd) | Мультиагентный пайплайн LangGraph: агенты, interrupt-чекпоинты, Critic-цикл |
| [`rag.mmd`](rag.mmd) | RAG-контур: ingest (Docling → Qdrant) → hybrid search → rerank → верификация |
| [`db-schema.mmd`](db-schema.mmd) | ER-схема PostgreSQL: users, courses, versions, jobs, events, references, feedback, usage |
| [`course-graph.mmd`](course-graph.mmd) | Доменная модель: компетенция → результат обучения → модуль → артефакты (constructive alignment) |
| [`llm-router.mmd`](llm-router.mmd) | Иерархия моделей (LiteLLM): сильная/дешёвая/reasoning + fallback и ретраи |
| [`job-states.mmd`](job-states.mmd) | State machine джоба: draft → running → waiting_input → ready/failed |
| [`deployment.mmd`](deployment.mmd) | Docker Compose деплой + CI-конвейер GitHub Actions |
| [`data-flow.mmd`](data-flow.mmd) | Sequence-диаграмма полного потока: бриф → чекпоинты → генерация → ZIP |

## Как рендерить

1. **VS Code:** расширение *Markdown Preview Mermaid Support* (поддерживает `.mmd`) или
   *Mermaid Preview* (экспорт в PNG/SVG).
2. **Онлайн:** открыть файл в [mermaid.live](https://mermaid.live) (Copy-paste).
3. **CLI (PNG/SVG):**
   ```bash
   npm i -g @mermaid-js/mermaid-cli
   mmdc -i diagrams/pipeline.mmd -o diagrams/pipeline.png -b white
   ```

## Автоматический экспорт в PNG/SVG

Если в проекте установлен Node.js, все диаграммы можно отрендерить разом:

```bash
npx @mermaid-js/mermaid-cli -i diagrams/architecture.mmd -o diagrams/architecture.png -b white
```

Либо добавить скрипт `render:diagrams` в package.json, который пройдётся по всем `.mmd`.

## Интеграция с plan.md

Ключевые диаграммы продублированы прямо в [`plan.md`](../plan.md) (§4 Архитектура, §8 RAG, §17 Демо).
Здесь лежат их расширенные версии + дополнительные схемы (БД, модель данных, состояния, деплой).