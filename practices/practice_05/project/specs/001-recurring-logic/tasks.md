# Tasks: Повторяющиеся дедлайны — логика

**Input**: [plan.md](plan.md), [data-model.md](data-model.md), [../contracts/recurring.md](../contracts/recurring.md)

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Foundational

- [x] T001 Тест миграции 1 → 2 на БД с данными (старые строки: recurrence/next_id = null) в tests/test_db.py
- [x] T002 `_migration_2` и поля `recurrence`, `next_id` в `Deadline` / `_deadline_from_row` в backend/db.py; T001 проходит

## Phase 2: User Story 1–2 — следующий экземпляр и граничные даты (P1) 🎯 MVP

- [x] T003 [P] [US2] Тест `next_due` по таблице Edge Cases spec.md (31-е, 29.02, переход года, daily/weekly) в tests/test_db.py
- [x] T004 [US2] `next_due()` в backend/db.py; T003 проходит
- [x] T005 [US1] Тесты правил: done создаёт ровно один, наследуемые поля, опоздание = один шаг, done/todo/done без дубля, удаление следующего → next_id null и пересоздание, POST done не создаёт, атомарность при выходе за 9999 год — tests/test_db.py
- [x] T006 [US1] `update_deadline_with_next` → `(deadline, next)` с созданием в одной транзакции; `create_deadline` пишет recurrence/recurrence_day; T005 проходит
- [x] T007 [US1] `server.update_deadline` отдаёт `next`; тест ответа PATCH (`next` полный / `null`) в tests/test_server.py

## Phase 3: User Story 3 — управление повтором и ошибки (P2)

- [x] T008 [US3] Тесты: POST/PATCH c recurrence, `null` выключает, смена due_at переустанавливает опорный день, ошибки `recurrence` (R5) и `next_id` (неизвестное поле) — tests/test_server.py
- [x] T009 [US3] Валидация `recurrence` и опорного дня в `_validate_deadline`; T008 проходит

## Phase 4: Polish

- [x] T010 [P] [US4] Тест: `.ics` без `RRULE`, stats после выполнения (`open` прежний, `done` +1) в tests/test_server.py
- [x] T011 README: поле `recurrence`/`next_id` и `next` в разделе API; `pyright` без ошибок
