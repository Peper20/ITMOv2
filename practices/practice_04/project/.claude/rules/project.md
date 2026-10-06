# Проект

Простой сайт: статический фронтенд (HTML/CSS/JS) + бэкенд на Python + SQLite.

## Структура
- `backend/` — Python-сервер (`server.py`) и работа с БД (`db.py`)
- `frontend/` — `index.html`, `style.css`, `app.js`
- `tests/` — тесты на `unittest`
- `data/` — файл БД `app.db` (в git не попадает)

## Принципы
- Никаких внешних зависимостей: только стандартная библиотека Python и «чистый» JS без сборщиков и CDN.
- Тесты: `python3 -m unittest discover tests`.
- Схему БД смотри через MCP-сервер `sqlite` (`db_schema`, `db_query`).
- Поиск по смыслу («где/как делается X») — через MCP-сервер `grepai` (`grepai_search`); точные имена и строки — через Grep.
