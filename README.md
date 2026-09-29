# Система знаний команды

Учебный RAG-сервис по заданию [`1st_prompt.md`](1st_prompt.md). Пользователь добавляет документы `.txt`/`.md` или текст, задаёт вопрос и получает ответ с источниками либо отказ с `needs_review=true` и причиной. Поиск объединяет pgvector и BM25 через RRF; решение о достаточности оснований принимает backend.

## Запуск

1. Скопируйте `.env.example` в `.env` и задайте `YANDEX_FOLDER_ID`, `YANDEX_API_KEY`. Ключу нужен доступ к моделям AI Studio.
2. Выполните `docker compose up --build -d`.
3. Откройте `http://localhost/documents`. Проверка сервиса: `http://localhost/health`.

Контейнер API запускает Alembic-миграции перед Uvicorn. PostgreSQL хранится в томе `postgres_data`. Только Caddy публикует порт `80`; API и БД не имеют внешних портов. Для API оставлен исходящий сетевой доступ к Yandex AI Studio. Один Uvicorn worker нужен для единого BM25-индекса в памяти.

Пороги `EVIDENCE_MAX_COSINE_DISTANCE=0.78`, `EVIDENCE_MIN_BM25_SCORE=2.0` и `LLM_MIN_CONFIDENCE=0.7` заданы в `.env` и передаются контейнеру через Compose. Параметры chunking, top-K, RRF и модели тоже настраиваются там; доступные имена приведены в `.env.example`. После изменения `.env` выполните `docker compose up -d`, чтобы пересоздать API. Пороговая политика утверждена для учебного набора из пяти документов; при другом корпусе её следует перепроверить.

## Контрольный набор и поиск

В `examples/demo_documents` лежат 5 вымышленных документов команды; вопросы и ожидаемая доступность ответа — в `examples/questions.json`. После настройки Yandex загрузите документы через UI либо выполните `docker compose exec -T api python -m scripts.diagnose --base-url http://api:8000 --load-fixtures`. Затем та же команда без `--load-fixtures` выводит top-3 по каждому вопросу с исходными диагностическими значениями. `--load-fixtures` добавляет документы в базу и при повторном запуске создаст дубликаты, поэтому используйте его один раз на чистой учебной базе.

После загрузки набора выполните `docker compose exec -T api python -m scripts.acceptance`. Скрипт проверит семь ответов с источниками, три отказа с причиной, историю и аудит. `POST /kb/retrieve` остаётся диагностическим контрактом с телом `{"question":"Когда выпускают релизы?"}`. Число RRF показывает порядок, а не уверенность ответа. Результаты выполненной приёмки записаны в `openspec/changes/archive/2026-09-29-0001-team-knowledge-mvp/`.

## API документов

- `GET /kb/documents` — список.
- `POST /kb/documents` — JSON `{"title":"...","text":"..."}`; документ появляется только после успешной индексации.
- `GET /kb/documents/{id}` — исходный текст.
- `DELETE /kb/documents/{id}` — удаление документа и его snippets.
- UI поддерживает вставку текста и UTF-8 файлы `.txt`/`.md`.

## API вопросов и истории

- `POST /kb/ask` и `POST /ai/answer_with_sources` — JSON `{"question":"..."}`; возвращают `answer`, `sources` с цитатами, `needs_review`, `review_reason`, `diagnostics`, `run_id`.
- `GET /kb/history` — последние 50 ответов; `?needs_review=true` оставляет требующие проверки.
- `GET /kb/audit` — последние 50 событий добавления/удаления документов и вопросов.
- Панель `/questions` показывает ответ, источник и причину проверки; `/history` — историю и аудит.

OpenAPI: `http://localhost/docs`. При отсутствии ключа или сбое Yandex загрузка/поиск вернут ошибку, документы частично не сохраняются.

## Локальные проверки

`python -m compileall -q app migrations scripts tests` и `docker compose config --quiet`. Unit-тесты с зависимостями контейнера: `docker compose exec -T api python -m unittest discover -s tests -v`. Интеграционный тест БД без вызова Yandex: `docker compose exec -T api python -m scripts.smoke`.
