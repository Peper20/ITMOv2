# Implementation Plan: Повторяющиеся дедлайны — логика

**Branch**: `001-recurring-logic` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)
**Input**: [spec.md](spec.md), общий контракт [../contracts/recurring.md](../contracts/recurring.md)

## Summary

Поле `recurrence` и ссылка `next_id` у дедлайна; при переходе в `done` в той же транзакции
создаётся следующий экземпляр со сроком на один шаг позже; PATCH возвращает его в поле `next`.

## Technical Context

**Language/Version**: Python 3.12+, только stdlib · **Storage**: SQLite, миграция `user_version` 1 → 2
**Testing**: `unittest` (`tests/test_db.py`, `tests/test_server.py`), pyright
**Project Type**: web-приложение (backend + frontend) · **Scale**: один пользователь, локально
**Research**: не требуется — все вопросы закрыты в spec.md → Clarifications.

## Constitution Check

| Принцип | Как соблюдается |
|---|---|
| I. Минимум зависимостей | `calendar.monthrange` и `datetime` из stdlib |
| II. Контракт API | поля и ошибки — по `contracts/recurring.md`, формат ошибок прежний |
| III. Тесты | таблица `next_due` из Edge Cases + сценарии API пишутся до кода |
| IV. Миграции | `_migration_2`: `ALTER TABLE ADD COLUMN` ×3, старые строки валидны (NULL) |
| V. Простота | без `series_id`, без пропуска периодов, без новых маршрутов |

## Project Structure

```text
backend/db.py      — _migration_2, next_due(), recurrence в валидации, update_deadline → (deadline, next)
backend/server.py  — update_deadline добавляет "next" в ответ
tests/test_db.py   — next_due (таблица), миграция 1→2, правила создания следующего
tests/test_server.py — POST/PATCH c recurrence, ошибки, next в ответе, .ics без RRULE
```

**Structure Decision**: существующая структура, новых модулей нет. Модель данных —
[data-model.md](data-model.md), проверка — [quickstart.md](quickstart.md).

## Decisions

- `next_due(due_at, recurrence, anchor_day)` — чистая функция; `monthly`/`yearly` через
  `calendar.monthrange`, день = `min(anchor_day, дней в месяце)`. Выход за 9999 год →
  `ValidationError("status", ...)`.
- `update_deadline` возвращает пару `(deadline, next | None)`, сервер собирает
  `{**deadline, "next": next}`. Альтернатива — флаг в `Deadline` — смешала бы постоянное поле с
  разовым.
- Отметка и вставка следующего — один `with conn:`; `next_id` ставится тем же UPDATE.

## Complexity Tracking

Нарушений constitution нет.
