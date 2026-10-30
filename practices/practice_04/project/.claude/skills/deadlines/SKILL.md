---
name: deadlines
description: Use when the user wants to add, change, reschedule, complete, delete or look up deadlines (дедлайны, сроки, задачи по учёбе/работе) or categories in the running «Сроки» tracker — through its HTTP API via the bundled CLI scripts/sroki.py. Not for changing the app's code.
---

# «Сроки»: работа с дедлайнами через API

«Сроки» — self-hosted трекер дедлайнов этого проекта: `backend/server.py` (Python stdlib + SQLite,
`data/app.db`) отдаёт JSON API под `/api` и календарь-фронтенд на `/`. Пользователь один,
авторизации нет. Сущности: **категории** (курс/проект) и **дедлайны** (срок, приоритет, статус).

Этот скилл — про **данные** в работающем приложении. Код приложения он не меняет.

## Порядок работы

1. Проверь сервер: `python3 .claude/skills/deadlines/scripts/sroki.py health`.
   Если он недоступен, предложи запустить `python3 backend/server.py` (порт 8000) в фоне.
   Адрес можно сменить через `SROKI_URL`.
2. Если запрос пользователя неоднозначен («перенеси лабу»), сначала найди кандидатов:
   `list --q лаба --status open`. Если подходят несколько — спроси, какой именно.
3. Выполни действие одной командой CLI и коротко сообщи результат: id, название, срок, категория.
4. **Удаление необратимо.** Удаляй только явно названный дедлайн. Если пользователь назвал его
   не по id, сначала покажи, что найдено, и получи подтверждение. Отметка «готово» (`done`)
   обратима (`reopen`) и подтверждения не требует.

## CLI `scripts/sroki.py` (только stdlib)

Запуск из корня проекта: `python3 .claude/skills/deadlines/scripts/sroki.py <команда>`.
Успех — JSON в stdout, код 0. Ошибка — `{"error", "field"?}` в stderr, код 1.

| Команда | Что делает |
|---|---|
| `health`, `stats`, `categories` | проверка сервера, сводка, список категорий |
| `list [--status todo\|in_progress\|done\|open] [--category X] [--q текст] [--from D] [--to D] [--sort due\|priority\|created]` | поиск дедлайнов |
| `get ID` | один дедлайн |
| `add "Название" [--due …] [--category X] [--priority …] [--description …]` | создать (без `--due` — завтра 23:59) |
| `update ID [--title] [--due] [--category X\|none] [--priority] [--status] [--description]` | частичное изменение |
| `done ID` / `reopen ID` | отметить выполненным / вернуть в работу |
| `delete ID` | удалить; в ответе — удалённый объект |

Удобства CLI поверх API:
- `--due`: `today`/`сегодня`, `tomorrow`/`завтра`, `+N` (через N дней), `YYYY-MM-DD` — все
  в 23:59; либо точно `YYYY-MM-DDTHH:MM`.
- `--category`: id, точное имя или уникальная подстрока имени без учёта регистра,
  `none` — без категории. Если совпадений нет или их несколько, CLI вернёт ошибку со
  списком вариантов.
- `--priority`: `1|2|3` или `low|normal|high`.

Пример: «добавь сдачу курсовой по ОС на 20 октября в 18:00, важно» →
`add "Сдать курсовую" --due 2026-10-20T18:00 --category "операционные" --priority high`.

## API (если CLI не подходит)

База `http://127.0.0.1:8000/api`, JSON в обе стороны. Полный контракт — `docs/PLAN.md`, раздел 3.

| Метод и путь | Тело / параметры | Ответ |
|---|---|---|
| `GET /health` | — | `{"status":"ok","version":"1"}` |
| `GET /categories` | — | массив Category, сортировка по имени |
| `POST /categories` | `{name, kind: study\|work\|other, color?: "#rrggbb"}` | 201 Category; дубль имени → 409 `field: "name"` |
| `PATCH /categories/{id}` | любые из `name, kind, color` | 200 Category |
| `DELETE /categories/{id}` | — | 204; дедлайны остаются без категории |
| `GET /deadlines` | `status` (`todo\|in_progress\|done\|open`), `category_id` (число\|`none`), `q`, `from`, `to` (`YYYY-MM-DD[THH:MM]`, включительно), `sort` (`due\|priority\|created`) | массив Deadline |
| `POST /deadlines` | `{title, due_at, description?, category_id?, priority?, status?}` | 201 Deadline |
| `GET /deadlines/{id}` | — | 200 Deadline |
| `PATCH /deadlines/{id}` | любые поля из POST; `category_id: null` снимает категорию | 200 Deadline |
| `DELETE /deadlines/{id}` | — | 204 |
| `GET /stats` | — | `{overdue, today, week, open, done}` |
| `GET /export.ics` | фильтры как у `/deadlines`, по умолчанию `status=open` | `text/calendar` |

Объекты:
- **Deadline** — `{id, title, description, due_at: "YYYY-MM-DDTHH:MM", category_id|null,
  priority: 1|2|3 (3 — высокий), status: todo|in_progress|done, created_at, updated_at,
  completed_at|null, is_overdue}`.
- **Category** — `{id, name, kind, color, created_at, open_count}`.

Правила валидации (сервер отвечает 400 с `field`):
- `title`: 1–200 символов;
- `description`: строка до 5000 символов, `null` не принимается;
- `due_at`: строго `YYYY-MM-DDTHH:MM`, время — локальное время сервера;
- `category_id` должен существовать;
- неизвестные поля запрещены.

Переход в `done` сам ставит `completed_at`, выход из `done` обнуляет его.

Ошибки: `{"error": "...", "field"?: "..."}`, коды 400, 404, 405, 409, 413 (тело больше 1 МБ), 500.
