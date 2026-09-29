# Система знаний команды

Учебный RAG-сервис по заданию [`1st_prompt.md`](1st_prompt.md). Текущая стадия: **CP3 — диагностика retrieval**. Сервис загружает текстовые документы, строит embeddings Yandex AI Studio и показывает результаты семантического поиска, BM25 и RRF. Генерация ответов и история вопросов появятся после обязательного согласования evidence policy.

## Запуск

1. Скопируйте `.env.example` в `.env` и задайте `YANDEX_FOLDER_ID`, `YANDEX_API_KEY`. Ключу нужен доступ к моделям AI Studio.
2. Выполните `docker compose up --build -d`.
3. Откройте `http://localhost/documents`. Проверка сервиса: `http://localhost/health`.

Контейнер API запускает Alembic-миграции перед Uvicorn. PostgreSQL хранится в томе `postgres_data`. Только Caddy публикует порт `80`; API и БД не имеют внешних портов. Для API оставлен исходящий сетевой доступ к Yandex AI Studio. Один Uvicorn worker нужен для единого BM25-индекса в памяти.

## Проверка поиска

В `examples/demo_documents` лежат 5 вымышленных документов команды; вопросы и ожидаемая доступность ответа — в `examples/questions.json`. После настройки Yandex загрузите документы через UI либо выполните `python scripts/diagnose.py --load-fixtures` с хоста. Затем `python scripts/diagnose.py` выводит top-3 по каждому вопросу с исходными диагностическими значениями. `--load-fixtures` добавляет документы в базу и при повторном запуске создаст дубликаты, поэтому используйте его один раз на чистой учебной базе.

До CP4 `POST /kb/retrieve` является диагностическим контрактом. Пример тела: `{"question":"Когда выпускают релизы?"}`. Число RRF показывает порядок, а не уверенность ответа. `POST /kb/ask` и `POST /ai/answer_with_sources` пока отсутствуют согласно checkpoint задания.

## API документов

- `GET /kb/documents` — список.
- `POST /kb/documents` — JSON `{"title":"...","text":"..."}`; документ появляется только после успешной индексации.
- `GET /kb/documents/{id}` — исходный текст.
- `DELETE /kb/documents/{id}` — удаление документа и его snippets.
- UI поддерживает вставку текста и UTF-8 файлы `.txt`/`.md`.

OpenAPI: `http://localhost/docs`. При отсутствии ключа или сбое Yandex загрузка/поиск вернут ошибку, документы частично не сохраняются.

## Локальные проверки

`python -m compileall -q app migrations scripts` и `docker compose config --quiet`. Unit-тесты: `python -m unittest discover -s tests`. Для них нужны зависимости из `requirements.txt`. Полный контрольный прогон CP3 требует ключа Yandex и запущенного Docker. Решение о порогах evidence принимается оператором после просмотра реальной диагностики.
