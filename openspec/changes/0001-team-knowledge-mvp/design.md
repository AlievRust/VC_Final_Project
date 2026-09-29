# Проектирование MVP

Источник требований: `1st_prompt.md`. `openspec/project.md` пуст; существующего приложения и тестов нет. Режим: STANDARD с обязательными checkpoint из задания.

## Контракты и компоненты

- Один FastAPI-процесс обслуживает JSON API и серверные Jinja2-страницы. Отдельного SPA нет.
- PostgreSQL хранит `documents`, `snippets`, `qa_runs`, `audit_runs`. Схему создаёт Alembic, приложение не выполняет `create_all`.
- Синхронный сервис загрузки: проверка текста/расширения → разбиение по абзацам → Yandex embeddings → одна транзакция записи документа и всех snippets. Внутри транзакции готовится снимок BM25, который публикуется только после commit. Сбой до commit не оставляет документ в KB.
- Один процесс Uvicorn и общий lock для записи и retrieval. На старте индекс читается из БД; после успешного добавления/удаления публикуется подготовленный снимок. Несколько workers не поддерживаются, пока индекс находится в памяти.
- Retrieval: отдельный SQL pgvector cosine search и `rank_bm25` по всем сохранённым snippets; RRF с параметром `k`, далее `fusion_top_k`. RRF — ранжирование, не мера уверенности.
- До решения CP3 API `POST /kb/retrieve` возвращает диагностические ранги, расстояния и BM25-score. `/kb/ask` и `/ai/answer_with_sources` появляются только в CP4.
- `GET /kb/documents`, `POST /kb/documents` (JSON: `title`, `text`), `GET /kb/documents/{id}`, `DELETE /kb/documents/{id}`. Загрузка `.txt`/`.md` через HTML-форму; оба входа используют один сервис.
- При CP4 модель получает только выбранные chunks, возвращает структурированные `answer`, `source_ids`, `confidence`, `insufficient_evidence`; backend строит `sources` из переданных snippets и принимает окончательное решение. Конкретный порог evidence сейчас не определён.
- Схема: `documents(id, title, text, created_at)`; `snippets(id, document_id ON DELETE CASCADE, chunk_index, text, embedding vector(256), created_at)` с уникальной парой `(document_id, chunk_index)`; `qa_runs` и `audit_runs` содержат JSON-диагностику и время. Удаление документа не удаляет исторический снимок источников в `qa_runs`.
- Caddy проксирует FastAPI. Только Caddy имеет `ports: ["80:80"]`; БД доступна только на внутренней Compose-сети `private`, API подключён к ней и к сети `edge` для Caddy и исходящих запросов Yandex. Том только для PostgreSQL.

## Решения

**D-01. 256 измерений и пара doc/query.** Используем модели `text-search-doc` и `text-search-query`; размер проверяется при каждом ответе API. Причина: официальная документация Yandex указывает 256 измерений для этой пары. Переход на v2 или иную размерность потребует миграции и переиндексации.

**D-02. Точный vector scan.** На учебном объёме выполняем `ORDER BY embedding <=> query LIMIT K` без ANN-индекса. Это сохраняет прозрачность поиска и не требует настройки индекса.

**D-03. Политика evidence отложена.** Нельзя выводить `strong/weak/none` из RRF. После прогона контрольных вопросов на реальных Yandex embeddings оператор утверждает признаки и пороги. До этого диагностика содержит исходные расстояния, лексические scores и ранги без итогового `needs_review`.

**D-04. Атомарная публикация BM25.** Новый индекс строится до commit из видимого состояния транзакции и публикуется после commit под lock. Ошибка подготовки индекса отменяет запись; поисковый запрос не смешивает vector- и BM25-снимки разных версий.

## Внешние контракты

- Yandex AI Studio, [Text vectorization models](https://aistudio.yandex.ru/en/docs/ai-studio/concepts/embeddings), прочитано 2026-09-29: URI пары `emb://<folder>/text-search-doc/latest` и `.../text-search-query/latest`, размер 256.
- Yandex AI Studio, [Embeddings.TextEmbedding REST](https://aistudio.yandex.ru/en/docs/ai-studio/embeddings/api-ref/Embeddings/textEmbedding), прочитано 2026-09-29: POST `https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding`, тело `modelUri`, `text`, ответ `embedding`.
- Yandex Cloud, [API key authentication](https://yandex.cloud/en/docs/iam/concepts/authorization/api-key), прочитано 2026-09-29: заголовок `Authorization: Api-Key <key>`.
- pgvector-python, [SQLAlchemy integration](https://github.com/pgvector/pgvector-python/blob/master/README.md), прочитано 2026-09-29: тип `VECTOR(256)` и метод `cosine_distance`.
- Yandex Cloud, [OpenAI-compatible endpoint](https://yandex.cloud/en/docs/tutorials/ml-ai/ai-model-ide-integration), прочитано 2026-09-29: базовый URL `https://ai.api.cloud.yandex.net/v1` и URI модели `gpt://<folder>/yandexgpt/latest`; понадобится в CP4.

## Базовое состояние и проверка

`git status --short --branch`: чистая ветка `main`; исходных тестов нет. Python 3.13.12 доступен; SQLAlchemy и остальные зависимости не установлены. Docker CLI и Compose доступны, Docker daemon недоступен (`docker_engine` не найден). До появления ключа Yandex и запущенного Docker интеграционная проверка БД и embeddings невозможна.

На CP1–CP3: compile Python, unit-тесты chunking/RRF/BM25 с фейковыми данными, `docker compose config`, затем по возможности интеграционный lifecycle в Docker. CP3 требует реального контрольного прогона для предложения порогов; синтетические embeddings не заменяют этот прогон.

## Фактически выполненные проверки CP1–CP3

- После запуска Docker пользователем локальный Compose стек собран и запущен. `curl http://127.0.0.1/health` вернул 200 и `{"status":"ok"}` через Caddy; страницы `/documents`, `/questions`, `/history` вернули 200.
- `docker compose ps` показал публикацию только `caddy: 0.0.0.0:80` и `[::]:80`; у `api` и `db` опубликованных портов нет.
- `python -m compileall -q app migrations scripts tests` и `docker compose config --quiet` прошли.
- `docker compose exec -T api python -m unittest discover -s tests -v`: 6 тестов прошли (границы chunk, BM25, RRF, выбор моделей Yandex и проверка размерности).
- `docker compose exec -T api python -m scripts.smoke`: добавление, SQL pgvector, BM25, RRF, каскадное удаление и аудит прошли с фейковыми векторами.
- Вызов `POST /kb/documents` без ключа Yandex вернул 502; `GET /kb/documents` остался пустым. Частичный документ не сохранился.
- `.env` отсутствует, ключ Yandex в окружении отсутствует. Реальные embeddings и 10 контрольных вопросов пока не проверены; численные пороги evidence по этим данным обосновать нельзя.
