# Tasks: Повторяющиеся дедлайны — UI

**Input**: [plan.md](plan.md), [../contracts/recurring.md](../contracts/recurring.md). Начинать после `001-recurring-logic`.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Foundational

- [ ] T001 Типы контракта в frontend/src/lib/api.ts (`Recurrence`, `recurrence`, `next_id`, ответ PATCH с `next`); `npm run check`
- [ ] T002 [P] `RECURRENCE_LABEL`, `describe()` с «повторяется …», `nextText()` в frontend/src/lib/deadlines.ts + тесты vitest

## Phase 2: User Story 1 — задать повтор в окне (P1) 🎯 MVP

- [ ] T003 [US1] Поле «Повтор» в DeadlineDialog.svelte после «Срок», до «Приоритет»; передаётся в POST/PATCH; ошибка `field=recurrence` под полем с фокусом; быстрое добавление без изменений

## Phase 3: User Story 2 — следующий после выполнения (P1)

- [ ] T004 [US2] `notice`, `afterUpdate()`, `showNext()` в app.svelte.ts; `setDone` и окно (кнопка и «Сохранить» со статусом «Выполнен») зовут `afterUpdate`
- [ ] T005 [US2] NextNotice.svelte: role=status, 8 с, пауза при наведении/фокусе, Esc/«Закрыть», «Показать» → день + подсветка; подключить в App.svelte
- [ ] T006 [US2] DeadlineCard: флажок неактивен на время запроса (FR-008), откат при ошибке

## Phase 4: User Story 3–4 — значок, снятие отметки (P2–P3)

- [ ] T007 [P] [US3] Иконка `repeat` в Icon.svelte; значок у открытых повторяющихся в Chip, DeadlineCard, Sidebar; подсказка «Повторяется …»; подсказка под полем в окне
- [ ] T008 [US4] Снятие отметки: «Следующий дедлайн на <дата> остался» / «Следующий дедлайн остался»; повторная отметка без сообщения

## Phase 5: Сквозная проверка

- [ ] T009 Сквозной сценарий quickstart.md в chromium: создание с повтором, отметка → следующий + «Показать», снятие → «остался», повторная отметка без дубля, 31.01 → 28.02, ошибка связи → откат; `npm test`, `npm run check`, `npm run build`
