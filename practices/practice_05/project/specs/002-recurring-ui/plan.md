# Implementation Plan: Повторяющиеся дедлайны — UI

**Branch**: `002-recurring-ui` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)
**Input**: [spec.md](spec.md), общий контракт [../contracts/recurring.md](../contracts/recurring.md)
**Depends on**: `001-recurring-logic` (поля `recurrence`, `next_id`, `next` в ответе PATCH)

## Summary

Поле «Повтор» в окне дедлайна, значок повтора на полоске/карточке/панели, неблокирующее
сообщение «Следующий — …» с «Показать» после отметки и «…остался» после снятия отметки.

## Technical Context

**Language/Version**: TypeScript, Svelte 5 (runes) · **Dependencies**: новых нет
**Testing**: vitest для чистых функций, svelte-check, сквозной сценарий в chromium (puppeteer-core)
**Research**: не требуется — вопросы закрыты в spec.md → Clarifications.

## Constitution Check

| Принцип | Как соблюдается |
|---|---|
| I. Зависимости | без новых npm-пакетов в приложении; puppeteer-core только для проверки вне проекта |
| II. Контракт | типы `Recurrence`, `Deadline.recurrence/next_id`, `UpdateResult.next` — из `contracts/recurring.md` |
| III. Тесты | подписи и тексты сообщения — чистые функции с vitest; сквозной сценарий в браузере |
| V. Простота | одно сообщение за раз, без диалогов о серии, дата следующего — только из ответа |

## Project Structure

```text
frontend/src/lib/api.ts             — Recurrence, поля Deadline, updateDeadline → Deadline & { next }
frontend/src/lib/deadlines.ts       — RECURRENCE_LABEL, recurrenceHint(), describe() + «повторяется …», nextText()
frontend/src/lib/app.svelte.ts      — notice (сообщение о следующем), afterUpdate(), showNotice()
frontend/src/components/NextNotice.svelte — сообщение: role=status, 8 с, пауза при наведении/фокусе, Esc, «Показать»
frontend/src/components/DeadlineDialog.svelte — поле «Повтор» после «Срок», подсказка, ошибка field=recurrence
frontend/src/components/{Chip,DeadlineCard,Sidebar}.svelte — значок повтора; Card: флажок неактивен во время запроса
frontend/src/components/Icon.svelte — иконка "repeat"
```

## Decisions

- Реакция на ответ PATCH в одной точке — `app.afterUpdate(before, result)`: `result.next` →
  «Следующий — …»; переход done → todo при `before.next_id` → «Следующий дедлайн … остался»
  (дата — из загруженных `deadlines`/`side`, иначе без даты). Её зовут и карточка, и окно.
- «Показать» = существующие `flashDate` + `navigateTo`, как переход из боковой панели.
- Сообщение — отдельный компонент рядом с `Banner`; `role="status"` (вежливо), фокус не
  забирает. Esc закрывает его, только если не открыто модальное окно.

## Complexity Tracking

Нарушений нет. Точка-режим месяца на телефоне значок не показывает (spec, Edge Cases).
