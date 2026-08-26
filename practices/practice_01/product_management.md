# Use cases и user stories

## Первый рабочий сценарий

**Когда** …, **система** …, **а пользователь получает** …

Не входит в этот сценарий:

- 

## Use case

| Поле | Значение |
|---|---|
| Актор |  |
| Триггер |  |
| Предусловия |  |
| Основной результат |  |
| Ошибка или отказ |  |

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant System as Система
    participant AI as AI
    User->>System: Событие или запрос
    System->>AI: Ограниченный вход и контекст
    AI-->>System: Предложение
    System-->>User: Проверяемый результат
```

## User stories и acceptance criteria

```gherkin
Feature:

  Scenario: Позитивный
    Given
    When
    Then

  Scenario: Негативный или граничный
    Given
    When
    Then
```

## Как использовали AI

- Для чего:
- Тип промпта:
- Строка в [`prompts.md`](prompts.md):
- Что проверили и исправили сами:
