---
paths:
  - "backend/db.py"
  - "backend/**/*.sql"
---

# SQLite

- Все запросы параметризованные (`?`), никакой подстановки строк через f-string.
- Соединение: `sqlite3.connect(path)`, `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`.
- Схема создаётся идемпотентно: `CREATE TABLE IF NOT EXISTS`.
- Тесты используют `:memory:` или временный файл, не `data/app.db`.
- Изменения схемы — через явную миграцию, а не правкой существующих таблиц «на месте».
