# Data Model: повторяющиеся дедлайны

Таблица `deadlines`, миграция 2 (`user_version` 1 → 2):

| Колонка | Тип | Ограничения | В API |
|---|---|---|---|
| `recurrence` | TEXT | NULL или `daily\|weekly\|monthly\|yearly` (CHECK) | `recurrence` (чтение/запись) |
| `recurrence_day` | INTEGER | NULL или 1–31 (CHECK); NOT NULL ⇔ `recurrence` NOT NULL | нет |
| `next_id` | INTEGER | `REFERENCES deadlines(id) ON DELETE SET NULL` | `next_id` (только чтение) |

Переходы статуса:

| Было → стало | `recurrence` | `next_id` | Эффект |
|---|---|---|---|
| todo/in_progress → done | не NULL | NULL | создать следующий, `next_id` = его id, `next` в ответе |
| todo/in_progress → done | не NULL | не NULL | ничего, `next: null` |
| done → todo/in_progress | любой | любой | только текущий; следующий остаётся |
| любое, без смены на done | — | — | `next: null` |

`recurrence_day` = день из `due_at`, когда в запросе есть `due_at` или ненулевой `recurrence`;
`recurrence: null` → `recurrence_day = NULL`. Следующий наследует `recurrence_day`.
