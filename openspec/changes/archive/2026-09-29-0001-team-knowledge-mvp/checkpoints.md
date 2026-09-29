# Checkpoints — 0001-team-knowledge-mvp

## Recovery capsule

- Режим: STANDARD; работа выполнена основным агентом.
- Текущий checkpoint: все CP0–CP6 `PASSED`; изменение завершено.
- Принятый дизайн: `design.md`, D-01–D-04 и P-01.
- Блокер: нет.
- Следующее действие: нет; изменение архивировано.
- User gate: P-01 утверждена оператором 2026-09-29 с требованием настройки порогов через `.env`.
- Независимый reviewer: не использовался; выполнена целевая самопроверка и интеграционные тесты.

## CP0 — Architecture & contracts

State: `PASSED`. Архитектурных противоречий не обнаружено; контракты и внешние источники в `design.md`.

## CP1 — Foundation

State: `PASSED`. FastAPI, миграция, Compose/Caddy, три страницы, healthcheck запущены. Проверки и топология: `design.md §Фактически выполненные проверки CP1–CP3`.

## CP2 — Documents & ingestion

State: `PASSED`. CRUD, chunking, REST adapter Yandex, хранение pgvector и атомарный BM25 реализованы. Интеграционный цикл с фейковыми векторами прошёл; позднее пять документов проиндексированы с реальными Yandex embeddings. Источники результата: `design.md §Фактически выполненные проверки CP1–CP3` и `§CP3`.

## CP3 — Retrieval

State: `PASSED`. Семантический поиск, BM25, RRF и диагностический `/kb/retrieve` реализованы. Unit и интеграционные проверки прошли. Пять документов и десять вопросов прогнаны с реальными Yandex embeddings; результаты P-01 в `design.md §CP3`, полный вывод в `cp3_diagnostics.txt`. После перезапуска API BM25 восстановился из PostgreSQL (`lexical_hits=1`, первый документ `03_incidents` для `P1`). Оператор утвердил P-01 и настройку порогов через `.env`.

## CP4 — Grounded answers

State: `PASSED`. ChatOpenAI, structured output, backend gate и два API реализованы. 11 unit-тестов прошли; реальные вопросы с ответом и без ответа проверены (`design.md §CP4`). Ключ хранится только в локальном `.env`.

## CP5 — History / audit / UI

State: `PASSED`. Ответы и события аудита сохраняются одной транзакцией; UI и API показывают источники, диагностику и фильтр `needs_review=true`. Интеграционные проверки прошли (`design.md §CP5`).

## CP6 — Acceptance

State: `PASSED`. На пяти документах `scripts/acceptance.py` проверил 10/10 вопросов: семь ответов с источниками и три отказа с причинами; история и аудит совпали с `run_id`. Тексты и цитаты просмотрены вручную. Проверки: 11 unit-тестов, smoke-тест БД/поиска, `compileall`, `docker compose config --quiet`, HTML-цикл `.md` загрузки/просмотра/удаления и `git diff --check`. Подробности — `design.md §CP6` и `cp6_acceptance.txt`. Независимый reviewer не применялся в режиме STANDARD.
