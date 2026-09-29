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

**D-03. Политика evidence утверждена оператором 2026-09-29.** Нельзя выводить `strong/weak/none` из RRF. По реальному прогону утверждено P-01 ниже; пороги должны настраиваться через `.env`.

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
- На момент этих проверок `.env` отсутствовал. После настройки пользователем выполнен отдельный живой прогон CP3 ниже.

## CP3: реальные результаты и предложение для оператора

2026-09-29 пользователь настроил локальный `.env`; значения не выводились и не записывались. API получил 256-мерный вектор от Yandex. REST-ответ для обеих моделей указал `modelVersion=06.12.2023`. В чистую учебную KB загружены пять файлов из `examples/demo_documents`, получившие ID документов 4–8; каждый содержит один snippet. Затем через `POST /kb/retrieve` прогнаны все десять вопросов из `examples/questions.json`. Полный вывод: [cp3_diagnostics.txt](cp3_diagnostics.txt).

| № | Ответ есть | Первый документ RRF | Cosine distance | BM25 | RRF | Условие ниже |
|---:|:---:|---|---:|---:|---:|:---:|
| 1 | да | onboarding | 0.746 | 5.861 | 0.03252 | strong |
| 2 | да | onboarding | 0.592 | 4.268 | 0.03279 | strong |
| 3 | да | leave | 0.458 | 5.316 | 0.03279 | strong |
| 4 | да | leave | 0.489 | 3.839 | 0.03279 | strong |
| 5 | да | incidents | 0.485 | 2.931 | 0.03279 | strong |
| 6 | да | releases | 0.453 | 3.199 | 0.03279 | strong |
| 7 | да | support | 0.636 | 2.661 | 0.03279 | strong |
| 8 | нет | onboarding | 0.820 | 1.394 | 0.03279 | weak |
| 9 | нет | leave | 0.729 | — | 0.01639 | weak |
| 10 | нет | releases | 0.713 | — | 0.01639 | weak |

**Утверждённая политика P-01.** Считать retrieval evidence `strong`, только если первый фрагмент после RRF одновременно присутствует в semantic и BM25 top-K, его cosine distance `<= 0.78`, а BM25 score `>= 2.0`. Если фрагменты есть, но условие не выполнено, ставить `weak`; если KB пуста, ставить `none`. Для `weak` и `none` backend всегда устанавливает `needs_review=true`; LLM не может отменить это решение. RRF остаётся исключительно сортировкой. Конкретный текст ответа и источники дополнительно проверяются в CP4 по контракту выше. Оператор утвердил условие с требованием вынести пороги в `.env`.

Обоснование на текущем наборе: максимальная дистанция у семи ответных первых фрагментов — `0.746`, минимальный BM25 — `2.661`; единственный неответный фрагмент с сигналами обоих retriever имеет `0.820` и `1.394`. Остальные два неответных не попали в BM25. Предложенное условие разделяет набор 7/3, но это **калибровка на тех же десяти вопросах**, не независимая оценка качества. BM25 зависит от состава корпуса, а URI моделей `/latest` может со временем измениться. Перед использованием на других документах пороги надо перепроверить.

## CP4: контракт ответа и проверка backend

- `POST /kb/ask` принимает JSON `{"question":"..."}` и возвращает `answer`, `sources`, `needs_review`, `review_reason`, `diagnostics`; `/ai/answer_with_sources` использует ту же схему и сервис.
- Для `weak/none` модель не вызывается: безопасный отказ с `needs_review=true`, пустыми источниками и причиной. Для `strong` первые `fusion_top_k` chunks передаются модели с их `snippet_id`, названием документа и текстом.
- LangChain `ChatOpenAI` подключается к OpenAI-compatible Chat Completions Yandex AI Studio. По умолчанию URI `gpt://<folder>/yandexgpt-5.1`; `ChatPromptTemplate` и JSON-schema structured output ограничивают форму ответа. Модель сообщает `answer`, `source_ids`, `confidence` от 0 до 1 и `insufficient_evidence`.
- Backend принимает ответ без review только если P-01 дала `strong`, текст ответа непуст, `insufficient_evidence=false`, `confidence >= LLM_MIN_CONFIDENCE`, список `source_ids` непуст и все ID принадлежат переданным модели chunks. Backend сам строит `sources` из этих chunks; цитаты модель не создаёт. При сбое любой проверки возвращается отказ с причиной, без чернового ответа модели.
- `EVIDENCE_MAX_COSINE_DISTANCE=0.78`, `EVIDENCE_MIN_BM25_SCORE=2.0`, `LLM_MIN_CONFIDENCE=0.7` и модель/параметры LLM находятся в конфигурации и передаются Compose из `.env`. Порог confidence 0.7 — консервативный начальный параметр, который проверяется в CP4/CP6; он не калиброван метриками retrieval.
- Внешние ошибки LLM дают HTTP 502 без текста запроса, содержимого документов и секрета в сообщении. История успешных вызовов и диагностические причины review сохраняются в CP5.
- При временных ошибках ChatOpenAI выполняет до двух повторов; журнал фиксирует только класс ошибки и HTTP-статус без ответа модели, содержимого документов и ключа.

Источники для CP4: Yandex AI Studio, [список доступных моделей](https://aistudio.yandex.ru/ru/docs/ai-studio/concepts/generation/models), прочитано 2026-09-29: `yandexgpt-5.1` доступен через OpenAI-compatible API. Yandex AI Studio, [структурированный запрос Chat Completions](https://aistudio.yandex.ru/ru/docs/ai-studio/operations/generation/completions-structured), прочитано 2026-09-29: `response_format=json_schema`, `max_tokens`, `temperature` и `OpenAI-Project` поддерживаются.

Проверка CP4: 11 unit-тестов прошли. Реальный `POST /kb/ask` на вопрос о P1 вернул `needs_review=false`, ответ «... в течение десяти минут после обнаружения» и источник `03_incidents` из переданного фрагмента. Вопрос о неизвестном бюджете вернул `needs_review=true`, пустые источники и причину по cosine distance; диагностика подтвердила отсутствие вызова модели. Значения `EVIDENCE_MAX_COSINE_DISTANCE`, `EVIDENCE_MIN_BM25_SCORE`, `LLM_MIN_CONFIDENCE` добавлены в локальный `.env` без вывода ключа и проходят через Compose.

## CP5: история и аудит

- Каждый успешный вызов `/kb/ask`, `/ai/answer_with_sources` или формы вопросов сохраняет снимок результата в `qa_runs`: вопрос, ответ, источники, `needs_review`, причина, диагностика. В той же транзакции появляется `audit_runs` с действием `question.asked` и ID записи. Ошибка внешней модели остаётся HTTP 502 и не выдаётся за ответ по KB.
- `GET /kb/history?needs_review=true` возвращает последние записи и фильтрует ручную проверку; `GET /kb/audit` показывает последние операции. Лимит 50 строк достаточен для учебной панели.
- Страница вопросов показывает ответ, статус, причину, цитаты и диагностику. Страница истории показывает эти же снимки и аудит `document.created`, `document.deleted`, `question.asked`. Удаление документа не меняет уже сохранённые источники истории.

Проверка CP5: два реальных запроса (`P1` и неизвестный бюджет) создали `qa_runs` и два события `question.asked`; фильтр `/kb/history?needs_review=true` показал отказ с причиной. HTML формы вопросов показал подтверждённый ответ и цитату `03_incidents`, а страница истории с фильтром — вопрос о бюджете и причину review.

## CP6: приёмочный прогон

Прогнать `examples/questions.json` через `/kb/ask` на пяти уже загруженных документах. Для семи `answerable=true` проверить `needs_review=false` и непустые источники; для трёх остальных — `needs_review=true` и понятную причину. Сверить все десять `run_id` с `/kb/history` и событиями `question.asked` в `/kb/audit`. Тексты ответов и цитаты просмотреть отдельно: бинарные признаки не доказывают фактическую корректность.

Проверка CP6: `docker compose exec -T api python -m scripts.acceptance` дал 10/10 PASS на пяти документах: семь ответов с корректными источниками и три отказа с понятными причинами; все `run_id` найдены в истории и аудите. Полный вывод — `cp6_acceptance.txt`. Ручная сверка каждого из семи ответов с приведённым фрагментом подтвердила содержание. Через UI пройден цикл загрузки, просмотра и удаления временного `.md` документа. Повторно прошли 11 unit-тестов, `scripts.smoke`, `compileall`, `docker compose config --quiet` и `git diff --check`; финальный `curl.exe --noproxy "*" http://127.0.0.1/health` вернул 200 OK через Caddy. Перед успешным прогоном был единичный HTTP 502 внешней модели для шестого вопроса; повтор этого вопроса и полный прогон прошли, для временных сбоев добавлены два повтора ChatOpenAI. Остаточный риск: пороги P-01 проверены только на учебном корпусе, внешняя модель может снова дать сбой; в этом случае API возвращает HTTP 502 без ложного ответа.
