# Диаграммы проекта

Набор Mermaid-диаграмм для ИИ-агента создания образовательных программ.
Все файлы — исходники в формате Mermaid (`.mmd`).

## Список диаграмм

| Файл | Что показывает |
|---|---|
| [`architecture.mmd`](architecture.mmd) | High-level архитектура: frontend, backend, сервисный слой, LangGraph, LLM-клиент, MLflow, MCP |
| [`pipeline.mmd`](pipeline.mmd) | Мультиагентный пайплайн: сделанный линейный срез (intake → competency → curriculum → validate) + план (Send, Critic, чекпоинты) |
| [`rag.mmd`](rag.mmd) | RAG-контур: ingest (Docling → Qdrant) → hybrid search → rerank → верификация (подробно: [`rag_plan.md`](../workflows/rag_plan.md)) |
| [`db-schema.mmd`](db-schema.mmd) | ER-схема PostgreSQL: users, courses, versions, jobs, events, references, feedback, usage |
| [`course-graph.mmd`](course-graph.mmd) | Доменная модель: компетенция → результат обучения → модуль → артефакты (constructive alignment) |
| [`llm-router.mmd`](llm-router.mmd) | LLM-клиент: иерархия моделей, structured output, fallback; LiteLLM — план |
| [`job-states.mmd`](job-states.mmd) | State machine курса и джобы (актуальные enum'ы) |
| [`deployment.mmd`](deployment.mmd) | Docker Compose деплой (postgres, qdrant, mlflow, mmdc) + CI |
| [`data-flow.mmd`](data-flow.mmd) | Sequence-диаграмма: бриф → сервисный слой → worker → SSE → версия курса |
| [`mcp.mmd`](mcp.mmd) | MCP-интеграция: сервер (FastMCP) + клиенты (langchain-mcp-adapters) |
| [`observability.mmd`](observability.mmd) | Observability: MLflow (трейсы, стоимость, evals, Prompt Registry) |
| [`diagram-engines.mmd`](diagram-engines.mmd) | Выбор движка диаграмм: Mermaid / D2 / Graphviz + кэш рендеров |
| [`rag.d2`](rag.d2) | **Тест D2** (не Mermaid): RAG-контур с лучшим контролем раскладки |

## D2 (тест)

[`rag.d2`](rag.d2) — экспериментальная диаграмма на D2. Рендер:

```bash
# установка: https://d2lang.com
d2 --layout dagre diagrams/rag.d2 diagrams/rag.svg
```

D2 даёт лучший контроль над раскладкой и выглядит «из коробки»; рассматриваем его как опцию
Visual Agent для архитектурных схем (см. [`diagram-engines.mmd`](diagram-engines.mmd)).

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

## Интеграция с планами

- [`plan.md`](../workflows/plan.md) — концепция, архитектура, RAG, демо.
- [`next-steps.md`](../workflows/next-steps.md) — рабочий план по этапам (актуальный).
- [`rag_plan.md`](../workflows/rag_plan.md) — подробный план RAG-контура.