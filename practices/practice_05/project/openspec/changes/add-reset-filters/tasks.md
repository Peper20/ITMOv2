# Tasks

## 1. Логика

- [ ] 1.1 Добавить `hasActiveFilters(category, q)` в `lib/deadlines.ts` и тесты в `deadlines.test.ts`; `npx vitest run` проходит
- [ ] 1.2 Добавить в `AppState` `hasFilters` ($derived) и `resetFilters()` (очистка + один `refresh()`); `npm run check` без ошибок

## 2. UI

- [ ] 2.1 Кнопка «Сбросить» в `Toolbar.svelte`: видна при `app.hasFilters`, отменяет debounce, сбрасывает, фокус на `#filter-q`; `npm run build` проходит
- [ ] 2.2 Ручная проверка сценариев spec в браузере (сброс, сброс во время набора, экспорт, вид/период)

## Workflow follow-up

- Sync specs и archive после приёмки человеком.
