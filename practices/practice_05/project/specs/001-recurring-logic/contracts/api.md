# Контракт API: повторяющиеся дедлайны (черновик, сторона логики)

> **Заменён** общим контрактом [../../contracts/recurring.md](../../contracts/recurring.md) (решения R1–R6, 2026-10-29). Этот черновик — исторический, расхождения (пропуск периодов, текст ошибки `recurrence`, отсутствие `next` в ответе PATCH) не действуют.

Изменение аддитивное: новые поля в объекте дедлайна, новые проверки; маршруты не меняются,
`API_VERSION` остаётся `"1"`. Формат ошибок прежний: `{"error": "...", "field": "..."}`.

## 1. Модель

Новые поля объекта `Deadline` (в ответах всех эндпоинтов, где он есть):

| Поле | Тип | Запись | Значения |
|------|-----|--------|----------|
| `recurrence` | `string \| null` | POST, PATCH | `null` (нет), `"daily"`, `"weekly"`, `"monthly"`, `"yearly"` |
| `next_id` | `int \| null` | только чтение | id экземпляра, созданного при выполнении этого; `null` — нет/удалён |

Служебная колонка `recurrence_day` (1–31, опорный день) в JSON не выдаётся и не принимается.

`DEADLINE_FIELDS` += `"recurrence"`. `next_id`/`recurrence_day` в теле запроса → существующая
ошибка «Неизвестное поле».

## 2. Миграция БД (`user_version` 1 → 2)

```sql
ALTER TABLE deadlines ADD COLUMN recurrence TEXT
  CHECK (recurrence IN ('daily','weekly','monthly','yearly'));
ALTER TABLE deadlines ADD COLUMN recurrence_day INTEGER
  CHECK (recurrence_day BETWEEN 1 AND 31);
ALTER TABLE deadlines ADD COLUMN next_id INTEGER
  REFERENCES deadlines(id) ON DELETE SET NULL;
PRAGMA user_version = 2;
```

Существующие строки получают `NULL` во всех трёх колонках — валидны и без повтора.
`recurrence_day` NOT NULL ⇔ `recurrence` NOT NULL (гарантирует код, не CHECK).

## 3. Алгоритм `next_due(due_at, recurrence, anchor_day, now) -> str`

Чистая функция в `backend/db.py`, время суток сохраняется.

- `daily`: +1 день; `weekly`: +7 дней.
- `monthly`: месяц +1 (декабрь → январь следующего года); день = `min(anchor_day, дней_в_месяце)`.
- `yearly`: год +1, месяц тот же; день = `min(anchor_day, дней_в_месяце)` (29.02 → 28.02 → … → 29.02).
- Пропуск прошедших периодов (по умолчанию, ждёт уточнения): шаг повторяется, пока результат
  `<= due_str(now)`. Если уточнение решит «без пропуска» — один шаг.
- Результат после 9999-12-31 → `ValidationError("status", ...)` (см. ошибки).

`anchor_day` устанавливается = день из `due_at`, когда пользователь в POST/PATCH передаёт
`due_at` или ненулевой `recurrence`; при `recurrence: null` → `NULL`. Сгенерированный
экземпляр наследует `recurrence_day` предыдущего.

## 4. Эндпоинты

### `POST /api/deadlines`

```json
{"title": "Отчёт", "due_at": "2027-01-31T23:59", "recurrence": "monthly"}
```
→ `201`, объект с `"recurrence": "monthly", "next_id": null`. Без `recurrence` → `null`.
Создание со `status: "done"` следующий **не** создаёт.

### `PATCH /api/deadlines/{id}`

- Переход статуса `todo|in_progress` → `done` при `recurrence != null` и `next_id IS NULL`
  (с учётом нового `recurrence` из того же запроса): в одной транзакции
  1. обновляется текущий (`status`, `completed_at`, `updated_at`);
  2. вставляется следующий: `title, description, category_id, priority, recurrence,
     recurrence_day` — копии, `due_at = next_due(...)`, `status = 'todo'`,
     `completed_at = NULL`, `created_at = updated_at = now`, `next_id = NULL`;
  3. текущему ставится `next_id = id нового`.
- Ответ `200` — текущий (выполненный) дедлайн с заполненным `next_id`:
  ```json
  {"id": 7, "status": "done", "recurrence": "monthly", "next_id": 8, "...": "..."}
  ```
  Клиент получает новый экземпляр через `GET /api/deadlines/8` или перезагрузкой списка.
- `done` → `todo|in_progress`: только текущий; `next_id` и следующий не трогаются.
- Повторный переход в `done` при `next_id != null`: следующий не создаётся.
- `{"recurrence": null}`: повтор выключен, `recurrence_day = NULL`; существующий `next_id` не меняется.
- Смена `recurrence`/`due_at` у выполненного дедлайна ничего не создаёт.
- Для вычисления пропуска периодов `update_deadline` получает `now` (из `Request.now`,
  в тестах — `App.clock`), как `get_deadline`/`stats`.

### `DELETE /api/deadlines/{id}`

Без изменений, `204`. У предыдущего экземпляра `next_id` становится `null` (FK `ON DELETE SET NULL`).

### `GET /api/deadlines`, `GET /api/deadlines/{id}`

Новые поля в каждом объекте. Фильтры и сортировки без изменений.

### `GET /api/stats`

Формат и формулы без изменений: экземпляры считаются как обычные дедлайны.
После выполнения повторяющегося: `open` без изменения (−1 +1), `done` +1; `overdue/today/week`
пересчитываются по сроку нового экземпляра.

### `GET /api/export.ics`

Без изменений формата: каждый экземпляр — отдельный `VEVENT` с `UID:deadline-{id}@sroki`,
`RRULE` не выводится (иначе календарь дублировал бы будущие экземпляры, которые сервер
создаёт сам). По умолчанию (`status=open`) выполненные экземпляры не выгружаются.

## 5. Ошибки

| Случай | HTTP | `field` | `error` |
|--------|------|---------|---------|
| `recurrence` не строка и не `null`, или не из списка | 400 | `recurrence` | `Допустимые значения: daily, weekly, monthly, yearly или null` |
| `next_id` / `recurrence_day` в теле | 400 | `next_id` / `recurrence_day` | `Неизвестное поле «next_id»` (существующий текст) |
| Следующий срок вне диапазона дат (> 9999-12-31) при переходе в `done` | 400 | `status` | `Невозможно вычислить следующий срок повтора` |
| Дедлайн не найден | 404 | — | `Дедлайн {id} не найден` (как сейчас) |

При любой ошибке транзакция откатывается: ни текущий, ни новый экземпляр не меняются.

## 6. Тесты (`tests/`, unittest)

- `test_db.py`: таблица `next_due` из spec.md (Edge Cases), включая 31-е, 29.02, переход года,
  пропуск периодов при фиксированном `now`; миграция v1 → v2 на БД с данными.
- `test_server.py`: POST/PATCH c `recurrence`, ошибка 400, переход в `done` создаёт ровно один
  экземпляр, цикл done/todo/done без дублей, удаление следующего → `next_id: null` и повторное
  создание, stats до/после, `.ics` без `RRULE`.
