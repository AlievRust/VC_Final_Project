# Checkpoints — 0001-team-knowledge-mvp

## Recovery capsule

- Режим: STANDARD; работа выполнена основным агентом.
- Текущий checkpoint: CP3 `REVIEW`.
- Принятый дизайн: `design.md`, D-01–D-04; CP0–CP2 `PASSED`.
- Блокер: нет локального ключа Yandex; реальный прогон 10 вопросов и предложение численных порогов ещё невозможны.
- Следующее действие: после настройки `.env` выполнить `python scripts/diagnose.py --load-fixtures` на чистой учебной БД, оценить диагностику и вынести evidence policy оператору.
- User gate: утверждение evidence policy после CP3; CP4 не начинать до решения.
- Независимый reviewer: не использовался; выполнена целевая самопроверка и интеграционные тесты.

## CP0 — Architecture & contracts

State: `PASSED`. Архитектурных противоречий не обнаружено; контракты и внешние источники в `design.md`.

## CP1 — Foundation

State: `PASSED`. FastAPI, миграция, Compose/Caddy, три страницы, healthcheck запущены. Проверки и топология: `design.md §Фактически выполненные проверки CP1–CP3`.

## CP2 — Documents & ingestion

State: `PASSED`. CRUD, chunking, REST adapter Yandex, хранение pgvector и атомарный BM25 реализованы. Интеграционный цикл с фейковыми векторами прошёл; живой Yandex вызов ожидает ключ. Источник результата: `design.md §Фактически выполненные проверки CP1–CP3`.

## CP3 — Retrieval

State: `REVIEW`. Семантический поиск, BM25, RRF и диагностический `/kb/retrieve` реализованы. Unit и интеграционные проверки прошли. Операционное evidence: `BLOCKED` отсутствием ключа Yandex. Контрольный набор создан, но реальные вопросы не прогнаны. User gate: `PENDING` — пороги и признаки evidence должны быть предложены по реальным результатам и утверждены оператором. CP3 не принят, CP4 не начинать.

## Будущие checkpoint

| CP | State | Цель | Зависимость / gate |
|---|---|---|---|
| CP4 | `PENDING` | Grounded answers | CP3 `PASSED` и утверждённая evidence policy |
| CP5 | `PENDING` | История, аудит, итоговый UI | CP4 `PASSED` |
| CP6 | `PENDING` | Приёмочный набор | CP5 `PASSED` |
