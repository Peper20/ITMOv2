# Design

## Context

Хэш пишет `AppState.#writeHash()` через `history.replaceState` при каждом изменении вида или
даты; читает его только `start()` через `parseHash`. Слушателя `hashchange` нет. Фильтры
меняются в `Toolbar` и применяются вызовом `app.refresh()`.

## Goals / Non-Goals

**Goals:** фильтры переживают перезагрузку и передаются ссылкой.

**Non-Goals:** реакция на ручную правку хэша без перезагрузки (`hashchange`), история браузера.

## Decisions

- `Route` расширяется полями `category` и `q`; `parseHash`/`formatHash` остаются чистыми
  функциями и покрываются vitest. Альтернатива — отдельный модуль для фильтров — дублирует
  разбор `URLSearchParams`.
- Запись: `refresh()` вызывает `#writeHash()` перед загрузкой, поэтому хэш обновляется в
  одной точке для поиска, категории и сброса. `replaceState`, а не `pushState`, чтобы каждая
  буква поиска не создавала запись в истории.
- Чтение: `start()` берёт фильтры из хэша до первого `reloadAll()`; проверка существования
  категории — уже существующая ветка в `loadCategories()`.

```mermaid
sequenceDiagram
    actor U as Пользователь
    participant T as Toolbar
    participant A as AppState
    participant H as location.hash
    participant API as /api/deadlines

    Note over U,API: Открытие страницы
    U->>H: открывает #35;view=…&date=…&cat=3&q=лаба
    A->>H: start(): parseHash()
    H-->>A: view, date, category, q
    A->>API: reloadAll() → categories, затем deadlines с фильтрами
    alt категории cat нет
        A->>A: loadCategories(): filterCategory = ""
    end

    Note over U,API: Изменение или сброс фильтра
    U->>T: категория / поиск (debounce) / «Сбросить»
    T->>A: refresh() или resetFilters()
    A->>H: #35;writeHash() (replaceState, без cat/q если пусто)
    A->>API: loadPeriod() + loadSide()
```

## Risks / Trade-offs

- [Кириллица в `q` кодируется в адресе] → `URLSearchParams` кодирует и декодирует сам.
