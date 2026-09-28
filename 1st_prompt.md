# Задача

Разработать учебный выпускной проект курса по вайб-кодингу: **«Система знаний команды»**.

Это небольшое веб-приложение с базой знаний и RAG-поиском. Пользователь добавляет внутренние документы, задаёт вопрос и получает ответ **только на основании найденных материалов**, с обязательным указанием источников.

Если достаточных оснований для ответа нет, система не должна додумывать ответ: необходимо вернуть `needs_review=true` и понятную причину.

Проект учебный. Требуется законченный MVP без лишней production-инфраструктуры.

---

## Основной стек

- Python
- FastAPI + Uvicorn
- PostgreSQL + pgvector
- Caddy как единственная наружная точка входа (http)
- Docker Compose
- LangChain — как тонкий интеграционный слой для LLM/embeddings
- Yandex AI Studio:
  - Alice AI / YandexGPT через OpenAI-compatible `ChatOpenAI`
  - Yandex embeddings
- lexical retrieval: `rank_bm25`
- semantic retrieval: pgvector
- объединение результатов: RRF (Reciprocal Rank Fusion)

Наружу публикуется только Caddy на HTTP `:80`.

FastAPI и PostgreSQL доступны только внутри приватной Docker-сети.

---

# Web UI

Нужно реализовать простую серверную веб-панель без отдельного SPA-фреймворка.

Три основных раздела.

### 1. Документы

Возможности:

- список документов;
- добавление документа;
- просмотр документа;
- удаление документа.

Для MVP поддерживать текст и файлы `.txt` / `.md`.

---

### 2. Вопросы

Это не conversational chatbot, а независимый формат **вопрос → ответ по KB**.

Пользователь вводит вопрос и получает:

- ответ;
- список использованных источников;
- цитаты;
- статус `needs_review`;
- при необходимости причину, почему система не считает evidence достаточным.

Истории диалога и conversational memory не требуется.

---

### 3. История / аудит

Показывать историю последних запросов:

- время;
- вопрос;
- ответ;
- источники;
- `needs_review`;
- причина ручной проверки;
- диагностическую информацию, полезную для понимания работы retrieval/LLM.

Должен быть фильтр по запросам `needs_review=true`.

Также сохранять аудит основных операций сервиса.

---

# API

Минимальные контракты:

- `POST /kb/documents`
- `GET /kb/documents`
- удаление документа;
- `POST /kb/ask`
- `POST /ai/answer_with_sources`

Контракты могут быть разумно расширены, но не должны ломать требования учебного задания.

Для `/kb/ask`:

- если `needs_review=false`, источники обязательно присутствуют;
- если источников нет, `needs_review=true`.

---

# Хранение данных

PostgreSQL является единственным persistent source of truth.

Минимальные сущности:

- `documents`
- `snippets`
- `qa_runs`
- `audit_runs`

`documents` хранит исходный текст.

`snippets` хранит поисковое представление документа:

- связь с документом;
- порядок chunk;
- текст chunk;
- embedding;
- необходимые технические поля.

Не создавать универсальную metadata-систему без необходимости.

Удаление документа должно каскадно удалять его snippets/embeddings.

---

# Ingestion

Ingestion синхронный.

Логика концептуально:

`validation → chunking → embeddings → transactional persistence`

Документ либо полностью проиндексирован, либо не появляется в KB.

Фоновые workers, очереди, Redis и состояния `pending/indexing/...` для MVP не нужны.

Chunking должен использовать естественные границы текста/абзацев и объединять небольшие фрагменты до разумного размера.

Конкретные алгоритмы и размеры chunk определить в ходе реализации.

---

# Hybrid retrieval

Использовать два независимых retriever:

1. semantic search через pgvector;
2. lexical search через `rank_bm25`.

Результаты объединять через **RRF — Reciprocal Rank Fusion**.

RRF используется только для итогового ranking и **не должен трактоваться как confidence score**.

BM25 index может храниться в памяти приложения.

PostgreSQL остаётся источником истины:

- при старте приложения BM25 index строится по сохранённым snippets;
- после добавления/удаления документов индекс перестраивается.

Для объёма учебного проекта оптимизация incremental BM25 index не требуется.

---

# Evidence и needs_review

Нужно разделить:

1. качество retrieval/evidence;
2. мнение LLM;
3. окончательное решение backend.

Retrieval должен формировать детерминированную оценку evidence, например концептуально:

- `strong`
- `weak`
- `none`

Конкретные thresholds не фиксировать заранее: их необходимо подобрать и обосновать по тестовому набору на отдельном checkpoint.

LLM получает вопрос и найденные chunks и возвращает structured output, включающий как минимум:

- answer;
- использованные IDs источников/chunks;
- confidence;
- признак недостаточности evidence.

**LLM не принимает окончательное решение о `needs_review`.**

Backend проверяет:

- достаточно ли retrieval evidence;
- существуют ли указанные моделью source IDs;
- действительно ли эти chunks передавались модели;
- присутствуют ли источники;
- не считает ли сама модель evidence недостаточным;
- не возвращён ли низкий confidence.

Принцип:

> Retrieval определяет наличие evidence.  
> LLM интерпретирует evidence.  
> Backend принимает окончательное решение, можно ли выдавать ответ без `needs_review`.

Модель не может отменить сомнение deterministic gate.

---

# Источники и цитаты

LLM не должна генерировать окончательный текст цитат как источник истины.

Модель возвращает IDs использованных chunks.

Backend самостоятельно формирует `sources` из реально найденных и переданных модели snippets:

- `document_id`;
- название документа;
- цитата/фрагмент.

Таким образом, нельзя получить выдуманный моделью источник.

---

# LangChain

Использовать LangChain точечно:

- интеграция `ChatOpenAI` с Yandex AI Studio;
- embeddings adapter;
- prompt templates;
- structured output/parsing.

Не строить всю бизнес-логику приложения вокруг LangChain.

Собственным кодом реализовать:

- hybrid retrieval orchestration;
- BM25;
- RRF;
- evidence evaluation;
- source validation;
- `needs_review`;
- audit.

---

# Конфигурация

Все параметры, которые предполагают tuning, должны быть централизованно настраиваемыми, а не захардкоженными внутри retrieval-кода.

В частности:

- chunk size / overlap;
- vector top-K;
- BM25 top-K;
- fusion top-K;
- RRF parameters;
- retrieval/evidence thresholds;
- модели embeddings/LLM;
- необходимые параметры LLM.

Использовать разумные defaults.

Не раздувать `.env` настройками, которые не имеют смысла менять при эксплуатации.

---

# Checkpoints

Работать по checkpoint-модели.

Не проходить критические архитектурные развилки самостоятельно, если решение существенно влияет на архитектуру или критерии приёмки. В таких случаях вынести варианты оператору.

## CP0 — Architecture & contracts

Проверить исходные требования и спроектировать:

- компоненты;
- DB schema;
- API contracts;
- Yandex adapters;
- retrieval pipeline;
- `needs_review` flow;
- Docker topology.

Остановиться на REVIEW перед существенной реализацией, если обнаружены архитектурные противоречия.

## CP1 — Foundation

Поднять:

- FastAPI;
- PostgreSQL + pgvector;
- migrations;
- Caddy;
- Docker Compose;
- skeleton трёх страниц;
- healthcheck.

Проверить, что наружу опубликован только Caddy.

## CP2 — Documents & ingestion

Реализовать:

- CRUD документов;
- chunking;
- embeddings;
- сохранение snippets/pgvector;
- BM25 lifecycle.

Проверить полный add/delete lifecycle.

## CP3 — Retrieval

Реализовать hybrid retrieval:

- vector;
- BM25;
- RRF.

На этом checkpoint **не подключать генерацию ответа как способ скрыть проблемы retrieval**.

Прогнать контрольные вопросы и показать диагностические результаты retrieval.

На основании этих результатов предложить evidence policy / thresholds оператору.

Остановиться на REVIEW для согласования.

## CP4 — Grounded answers

После утверждения retrieval policy добавить:

- Alice AI;
- structured output;
- source validation;
- backend decision gate;
- `/kb/ask`;
- `/ai/answer_with_sources`.

Проверить отдельно answerable и unanswerable сценарии.

## CP5 — History / audit / UI

Довести:

- `qa_runs`;
- `audit_runs`;
- историю вопросов;
- фильтрацию `needs_review`;
- просмотр ответа, источников и причины review;
- итоговый UI.

## CP6 — Acceptance

Подготовить и прогнать предусмотренный заданием тестовый набор:

- 5 тестовых документов;
- 10 контрольных вопросов;
- 7 вопросов с ответом в KB;
- 3 вопроса без достаточного ответа.

Критерий:

- для 7 answerable вопросов: `needs_review=false`, источники присутствуют;
- для 3 unanswerable: `needs_review=true`, система честно сообщает о недостатке данных;
- запросы и причины review сохраняются в истории/аудите.

---

# Non-goals

Для MVP не добавлять без явной необходимости:

- authentication / authorization;
- роли;
- HTTPS/TLS;
- fail2ban;
- Redis;
- Celery/worker queues;
- Elasticsearch;
- отдельный frontend framework;
- monitoring stack;
- PDF/DOCX parsing;
- conversational memory;
- сложный reindex/version-management workflow.

Не добавлять инфраструктуру или зависимости только ради «production-like» архитектуры.

---

# Общий принцип работы

Это учебный проект, поэтому предпочтительны простые, прозрачные и объяснимые решения. Обязательны пояснения и докстринги.

На критических архитектурных развилках и особенно при выборе evidence thresholds после CP3 — остановись и запроси решение оператора.

Главная цель — получить небольшой, воспроизводимый и понятный end-to-end RAG-сервис, устройство которого можно объяснить на защите без скрытой магии фреймворков.