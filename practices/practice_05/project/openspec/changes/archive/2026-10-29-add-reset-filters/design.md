# Design

## Context

Фильтры живут в `AppState` (`filterCategory`, `q`), из них выводятся `filters` и `exportHref`.
Поиск в `Toolbar.svelte` запускает `app.refresh()` через debounce 300 мс (таймер локальный
в компоненте). Фильтры не попадают в хэш и `localStorage`.

## Goals / Non-Goals

**Goals:** одна кнопка, один запрос перезагрузки, без гонки с debounce.

**Non-Goals:** горячая клавиша, сохранение фильтров, изменения бэкенда.

## Decisions

- Признак активности — чистая функция `hasActiveFilters(category, q)` в `lib/deadlines.ts`,
  чтобы покрыть её vitest без компонента. `AppState` использует её в `$derived`.
- Сброс делает `Toolbar`: он владеет таймером debounce, поэтому сам отменяет его, затем зовёт
  `app.resetFilters()` и ставит фокус на `#filter-q`. Альтернатива — перенести таймер в
  `AppState` — шире, чем нужно.
- Кнопка внутри `<form role="search">`, `type="button"`, чтобы не вызывать submit.

## Risks / Trade-offs

- [Кнопка появляется и исчезает → сдвиг верстки] → кнопка в конце строки фильтров.
