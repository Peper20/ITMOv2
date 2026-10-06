# Проект

Простой сайт: фронтенд на Svelte + Vite (собирается в статику) + бэкенд на Python + SQLite.

## Структура
- `backend/` — Python-сервер (`server.py`) и работа с БД (`db.py`)
- `frontend/` — Svelte-приложение (`src/`), сборка в `frontend/dist/` (в git не попадает)
- `tests/` — тесты на `unittest`
- `data/` — файл БД `app.db` (в git не попадает)

## Принципы
- Бэкенд — только стандартная библиотека Python. Фронтенд — npm-зависимости по списку из
  `.claude/rules/frontend.md`, без CDN и внешних запросов в рантайме.
- Тесты: `python3 -m unittest discover tests`; фронтенд — `npm test` в `frontend/`.
- Схему БД смотри через MCP-сервер `sqlite` (`db_schema`, `db_query`).
- Поиск по смыслу («где/как делается X») — через MCP-сервер `grepai` (`grepai_search`); точные имена и строки — через Grep.
