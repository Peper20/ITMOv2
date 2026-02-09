# Практика 03: Управление кодинг-агентами (Cursor AI)

**Связь с лекцией:** Делегирование задач AI-агентам через контекст, правила и multi-chat workflow

## Цель семинара

- Научиться делегировать задачи кодинг-агенту (на примере Cursor AI)
- Освоить техники управления контекстом (@file, @codebase, фильтрация)
- Использовать правила (.cursorrules) для consistency кода
- Применить multi-chat workflow для изоляции задач
- Познакомиться с auto-run режимом для автоматизации

## Ожидаемые результаты

Студенты создадут работающий MVP микросервиса WeatherService на FastAPI:
- REST API с эндпоинтами для подписки на погоду (POST /subscribe, GET /subscriptions)
- Модели данных на Pydantic v2
- Хранение данных в памяти (In-memory storage)
- Журнал Context & Rules Log с анализом техник управления AI-агентом
- Скриншот успешной работы API в Swagger UI
- **Домашнее задание:** Создание `Agents.md` для Практики 4

---

## 1. Вступление (5 минут)

### Цель блока
Показать проблему ручного кодинга и решение через делегирование AI-агенту.

### Что говорит преподаватель
- «Представьте: вам нужно написать FastAPI приложение с Pydantic моделями, валидацией, эндпоинтами. Раньше — часы работы. Сейчас — минуты, если правильно управлять AI»
- «Cursor AI — это не просто автодополнение. Это ваш стажер, который работает 24/7. Ваша задача — давать ему правильный контекст и правила»
- «Сегодня научимся трём вещам: как давать контекст, как задавать правила, как изолировать задачи через multi-chat»

### Что показывать на экране
- Слайд с целями семинара
- Быстрая демонстрация: пустой файл → промпт → рабочий код за 30 секунд
- Интерфейс Cursor: Command+K (Inline Edit), Command+L (Chat), @-символы

### Инструкции студентам
- Установите Cursor (если еще не установлен): https://cursor.com
- Создайте папку проекта: `mkdir WeatherService && cd WeatherService`
- Откройте в Cursor: `cursor .`
- Создайте виртуальное окружение: `python -m venv venv`
- Активируйте: `source venv/bin/activate` (Mac/Linux) или `venv\Scripts\activate` (Windows)
- Установите зависимости: `pip install fastapi uvicorn pydantic[email]`

### Техники вовлечения
- Вопрос: «Кто из вас уже пробовал GitHub Copilot или Cursor? Что было сложно?»
- Быстрый опрос: «Поднимите руку, если писали FastAPI вручную. Сколько времени заняло?»

---

## 2. Задание 1 — Управление контекстом (20 минут)

### Цель блока
Научиться использовать @file, @codebase, фильтрацию для управления контекстом AI-агента.

### Материалы
- Пустой проект с виртуальным окружением
- FastAPI и Uvicorn установлены

### Что говорит преподаватель
- «Контекст — это всё, что видит AI. Если вы не дадите ему нужные файлы, он будет галлюцинировать»
- «Три инструмента контекста в Cursor:
  1. **@file** — добавить конкретный файл (используйте, когда знаете, что нужно)
  2. **@codebase** — поиск по всему проекту (используйте для вопросов типа "где используется X?")
  3. **Фильтрация** — исключение файлов (например, venv, node_modules)»
- «Золотое правило: минимальный необходимый контекст. Не перегружайте AI ненужными файлами»

### Что показывать на экране
- Демонстрация @file: создание models.py с Pydantic моделью
- Демонстрация фильтрации: исключение venv из контекста
- Пример структуры проекта:
  ```
  WeatherService/
  ├── main.py
  ├── models.py
  ├── venv/ (excluded)
  └── .cursorrules (создадим позже)
  ```

### Инструкции студентам

**Шаг 1: Создание модели с @file**
1. Создайте пустой файл `models.py`
2. Откройте Cursor Chat (Command+L)
3. Введите промпт:
   ```
   @models.py Создай Pydantic v2 модель для подписки на погоду:
   - Название: Subscription
   - Поля:
     * city: str (не может быть пустым)
     * email: EmailStr (валидный email)
   - Добавь валидатор: city должен начинаться с заглавной буквы
   ```
4. Примените сгенерированный код
5. **Запишите промпт в `task.py` → `CONTEXT_LOGS`** (структура будет предоставлена)

**Шаг 2: Создание main.py с reference на models.py**
1. Создайте пустой файл `main.py`
2. В Cursor Chat:
   ```
   @models.py Создай FastAPI приложение в main.py:
   - Импортируй модель Subscription из models.py
   - Добавь health-check эндпоинт: GET /health → {"status": "ok"}
   - Используй Pydantic settings для конфигурации
   ```
3. Примените код
4. Запишите промпт в `CONTEXT_LOGS`

**Шаг 3: Проверка и фильтрация**
1. Убедитесь, что venv исключен из контекста:
   - Настройки Cursor → Ignored Files → добавить `venv/`, `__pycache__/`, `*.pyc`
2. Проверьте работу: `uvicorn main:app --reload`
3. Откройте http://localhost:8000/health

### Техники вовлечения
- Чекпоинт на 10-й минуте: «У кого уже сгенерировалась модель с валидатором?»
- Обмен опытом: «Попробуйте промпт без @models.py — что изменилось?»

### Ожидаемый артефакт
- Файл `models.py` с Pydantic моделью Subscription (с валидатором)
- Файл `main.py` с FastAPI приложением и health-check
- Запись в `CONTEXT_LOGS` с анализом: какой контекст помог, какой нет

### Пример записи в журнале
```python
ContextLog(
    task="Creating Pydantic model",
    context_used="@models.py",
    prompt="@models.py Создай Pydantic v2 модель Subscription...",
    result="Generated model with EmailStr and custom validator",
    analysis="@file помог AI понять, куда писать код. Без @models.py он создал бы код в chat."
)
```

---

## 3. Задание 2 — Правила для consistency (25 минут)

### Цель блока
Создать `.cursorrules` для единообразия кода и изучить три типа правил.

### Материалы
- Рабочий проект из Задания 1
- Примеры .cursorrules

### Что говорит преподаватель
- «Правила — это инструкции для AI, которые применяются автоматически. Три типа:
  1. **Manual rules** — вы вручную прикрепляете через @rules (полный контроль)
  2. **Auto-attached rules** — Cursor прикрепляет автоматически при релевантности (умный режим)
  3. **Always-included rules** — в каждом запросе (для критичных правил)»
- «`.cursorrules` — это файл в корне проекта. Cursor читает его автоматически»
- «Золотое правило: правила должны быть конкретными. Не "пиши хороший код", а "используй Pydantic v2 validators для валидации"»

### Что показывать на экране
- Пример `.cursorrules`:
  ```
  # WeatherService Project Rules

  ## Code Style
  - Use Pydantic v2 for all data models
  - All API endpoints must have type hints
  - Use async/await for I/O operations

  ## Naming Conventions
  - Models: PascalCase (e.g., Subscription)
  - Functions: snake_case (e.g., create_subscription)
  - API routes: kebab-case (e.g., /api/weather-data)

  ## Error Handling
  - Use FastAPI HTTPException for API errors
  - Always return meaningful error messages
  - Log errors with context

  ## Testing
  - Write docstrings for all public functions
  - Include example usage in docstrings
  ```

### Инструкции студентам

**Шаг 1: Создание .cursorrules**
1. Создайте файл `.cursorrules` в корне проекта
2. Скопируйте пример выше или создайте свой
3. Добавьте специфичные правила для вашего проекта

**Шаг 2: Тестирование правил через создание эндпоинта**
1. Откройте Cursor Chat (Command+L)
2. Введите промпт БЕЗ явного упоминания правил:
   ```
   @main.py @models.py Добавь POST /subscribe эндпоинт:
   - Принимает Subscription модель
   - Сохраняет в глобальный список subscriptions
   - Валидация: email уникальный
   - Возвращает созданную подписку
   ```
3. **Проверьте:** AI должен автоматически применить правила из `.cursorrules` (async, HTTPException, type hints)
4. Запишите в `RULES_LOGS`

**Шаг 3: Сравнение с ручным прикреплением**
1. Попробуйте явно прикрепить правила:
   ```
   @.cursorrules @main.py Добавь GET /subscriptions эндпоинт
   ```
2. Сравните результат: есть ли разница?
3. Запишите выводы в `RULES_LOGS`

### Техники вовлечения
- Через 15 минут: «Обменяйтесь .cursorrules с соседом — найдите лучшие правила»
- «Эксперимент»: попросите AI нарушить правило (например, "не используй type hints") — что произойдет?

### Ожидаемый артефакт
- Файл `.cursorrules` с минимум 5 правилами
- Эндпоинты POST /subscribe и GET /subscriptions в `main.py`
- Запись в `RULES_LOGS` с анализом применения правил

### Пример записи в журнале
```python
RuleLog(
    rule_type="auto-attached",
    rule="Use Pydantic v2 validators",
    task="Creating POST /subscribe endpoint",
    applied=True,
    result="AI automatically used validator_mode='after'",
    analysis="Auto-attached работает для явных задач. Для edge cases лучше @.cursorrules."
)
```

---

## 4. Задание 3 — Multi-chat workflow (25 минут)

### Цель блока
Научиться изолировать задачи через отдельные чаты для избежания смешения контекста.

### Материалы
- Рабочий проект с эндпоинтами из Задания 2

### Что говорит преподаватель
- «Проблема: один длинный чат → AI путается в контексте. Решение: multi-chat workflow»
- «Правило: **1 чат = 1 задача**. Примеры:
  - Chat 1: Создание моделей
  - Chat 2: Создание API эндпоинтов
  - Chat 3: Добавление валидации и error handling»
- «Когда создавать новый чат:
  - Смена задачи (models → API → tests)
  - Ошибка, которую не удается исправить за 2-3 итерации
  - Переключение между подсистемами»

### Что показывать на экране
- Демонстрация создания нового чата в Cursor
- Пример сценария:
  ```
  Chat 1 (Models): Создание Pydantic моделей
  Chat 2 (API): Создание FastAPI эндпоинтов
  Chat 3 (Validation): Добавление custom валидаторов
  ```

### Инструкции студентам

**Задача: Добавить 3 новых функции через 3 отдельных чата**

**Chat 1: DELETE /subscribe/{email}**
1. Создайте новый чат (Command+Shift+L)
2. Промпт:
   ```
   @main.py @models.py Добавь DELETE /subscribe/{email}:
   - Удаляет подписку по email
   - Если не найден: HTTPException 404
   - Возвращает {"message": "Unsubscribed"}
   ```
3. Примените код
4. Закройте чат (важно!)

**Chat 2: Добавление response models**
1. Создайте НОВЫЙ чат
2. Промпт:
   ```
   @models.py Создай Pydantic response models:
   - SubscriptionResponse (с полями: city, email, created_at)
   - MessageResponse (с полем: message)
   ```
3. Примените код

**Chat 3: Обновление эндпоинтов с response models**
1. Создайте НОВЫЙ чат
2. Промпт:
   ```
   @main.py @models.py Обнови все эндпоинты:
   - POST /subscribe → response_model=SubscriptionResponse
   - GET /subscriptions → response_model=List[SubscriptionResponse]
   - DELETE /subscribe/{email} → response_model=MessageResponse
   ```
3. Примените код

**Важно:** Запишите в `MULTICHAT_LOGS` для каждого чата:
- Какая задача
- Почему выбран отдельный чат
- Результат

### Техники вовлечения
- Чекпоинт на 15-й минуте: «У кого уже 3 отдельных чата?»
- «Провокация»: попросите студента сделать все задачи в одном чате — что произойдет?

### Ожидаемый артефакт
- 3 новых функции (DELETE endpoint, response models, updated endpoints)
- Минимум 3 записи в `MULTICHAT_LOGS`
- Скриншот Swagger UI с обновленными эндпоинтами

### Пример записи в журнале
```python
MultiChatLog(
    chat_number=1,
    task="DELETE /subscribe/{email}",
    reason="Isolated task: adding new endpoint without mixing context from validation chat",
    result="Successfully created DELETE endpoint with 404 handling",
    context_size="Small (only @main.py, @models.py)",
    analysis="Separate chat prevented AI from suggesting changes to validation logic from previous chat."
)
```

---

## 5. Демонстрация — Auto-run режим (10 минут)

### Цель блока
Показать, когда использовать и когда НЕ использовать auto-run режим.

### Что говорит преподаватель
- «Auto-run — режим, где AI автоматически выполняет команды (например, запуск тестов). Удобно, но опасно»
- «Когда использовать:
  - Повторяющиеся задачи (запуск тестов, линтеров)
  - Безопасные команды (read-only операции)»
- «Когда НЕ использовать:
  - Команды с побочными эффектами (удаление файлов, git push)
  - Первый запуск (всегда проверяйте вручную)»

### Что показывать на экране
- Включение auto-run в Cursor (Settings → Agent → Auto-run)
- Демонстрация безопасного сценария:
  ```
  Промпт: "Run uvicorn and check if /health endpoint works"
  Auto-run: uvicorn main:app --reload
  AI checks: curl http://localhost:8000/health
  ```
- Демонстрация опасного сценария (НЕ выполнять):
  ```
  Промпт: "Delete all .pyc files"
  Auto-run: find . -name "*.pyc" -delete  ← ОПАСНО без проверки
  ```

### Инструкции студентам
1. **НЕ включайте auto-run** для этого семинара
2. Запишите в `REFLECTION`:
   - Когда бы вы использовали auto-run?
   - Какие риски видите?

### Техники вовлечения
- Вопрос: «Кто готов доверить AI выполнение команд без проверки?»
- Обсуждение: «Какие команды безопасны для auto-run?»

---

## 6. Рефлексия и демонстрация (5 минут)

### Цель блока
Проанализировать опыт работы с AI-агентом и подготовиться к созданию Agents.md.

### Что говорит преподаватель
- «Заполните секцию `REFLECTION` в `task.py`: что узнали про контекст, правила, multi-chat»
- «Подумайте: какие правила и контекст вы бы хотели зафиксировать в одном файле для всего проекта?»
- «Это подводка к домашнему заданию: вы создадите `Agents.md` — единый источник правды для AI»

### Инструкции студентам
1. Заполните `REFLECTION` в `task.py`
2. Протестируйте все эндпоинты через Swagger UI (http://localhost:8000/docs)
3. Сделайте скриншот успешных запросов
4. Сохраните скриншот в папку проекта

### Демонстрация результатов
- Выбор 1-2 студентов для показа работающего API
- Показать не только результат, но и журналы (CONTEXT_LOGS, RULES_LOGS, MULTICHAT_LOGS)

---

## 7. Домашнее задание

### Обязательное

**Задача 1: Создание Agents.md для Практики 4**

Создайте файл `Agents.md` в корне проекта WeatherService со следующей структурой:

```markdown
# WeatherService - Спецификация проекта

## 📋 Project Overview
**Название:** WeatherService
**Описание:** REST API для подписки на уведомления о погоде
**Целевая аудитория:** Разработчики мобильных и веб-приложений

## 🛠 Tech Stack
- **Backend:** FastAPI (Python 3.11+)
- **Database:** SQLite (aiosqlite для async)
- **Validation:** Pydantic v2
- **External API:** OpenWeatherMap API
- **HTTP Client:** httpx (async)

## 🏗 Architecture

### Компоненты:
1. **API Layer** (main.py):
   - POST /subscribe — создание подписки
   - GET /subscriptions — список подписок
   - DELETE /subscribe/{email} — удаление подписки
   - GET /weather/{city} — получение погоды

2. **Models** (models.py):
   - Subscription (city, email, created_at)
   - WeatherData (city, temperature, description)

3. **Database** (database.py):
   - SQLite connection pool
   - CRUD операции для subscriptions

4. **External API** (weather_service.py):
   - Интеграция с OpenWeatherMap
   - Кэширование запросов (опционально)

## 📐 Development Rules

### Code Style:
- Используй Pydantic v2 для всех моделей
- Все функции с type hints
- Async/await для I/O операций
- HTTPException для ошибок API

### Naming:
- Models: PascalCase (Subscription)
- Functions: snake_case (create_subscription)
- Routes: /kebab-case

### Database:
- Используй aiosqlite для async операций
- Все миграции вручную (без Alembic для простоты)
- Таблица: subscriptions (id, city, email, created_at)

## 🎯 Current Tasks
1. [ ] Миграция с in-memory на SQLite
2. [ ] Интеграция с OpenWeatherMap API
3. [ ] Добавление тестов (pytest + httpx)

## 📝 Notes
- В Практике 4 используй этот файл как @Agents.md для всех промптов
- При добавлении новых фич — обновляй этот файл первым
```

**Требования:**
- Файл должен быть корректным Markdown
- Все секции заполнены
- Соответствует вашему текущему коду

**Задача 2: Журнал работы**
Заполните `task.py` со всеми логами (CONTEXT_LOGS, RULES_LOGS, MULTICHAT_LOGS, REFLECTION)

### Со звёздочкой (*)

**Задача: MCP Integration (опционально)**

Если у вас установлен MCP для Cursor:
1. Подключите MCP-сервер для работы с файловой системой
2. Используйте MCP для автоматического обновления `Agents.md` при изменении кода
3. Запишите опыт в отдельную секцию `MCP_EXPERIENCE` в `task.py`

**Подсказка:** MCP подробно разберем в Практике 4.

---

## Критерии оценки

| Критерий | Баллы | Что проверяется |
|:---|:---:|:---|
| **Рабочий API** | 3 | Все эндпоинты работают, Swagger UI доступен |
| **Журналы (CONTEXT_LOGS, RULES_LOGS, MULTICHAT_LOGS)** | 4 | Видно понимание техник управления AI |
| **.cursorrules** | 2 | Минимум 5 правил, применяются автоматически |
| **Agents.md (домашнее)** | 2 | Корректная структура, соответствие коду |
| **Рефлексия** | 1 | Анализ сильных/слабых сторон техник |
| **Всего** | **12** | |

---

## Дополнительные материалы

- Cursor Documentation: https://docs.cursor.com
- Pydantic v2 Validators: https://docs.pydantic.dev/latest/concepts/validators/
- FastAPI Best Practices: https://fastapi.tiangolo.com/tutorial/

## Troubleshooting

**Проблема:** AI не применяет .cursorrules
- **Решение:** Проверьте, что файл в корне проекта и корректный Markdown

**Проблема:** Контекст слишком большой (ошибка token limit)
- **Решение:** Используйте фильтрацию, исключите venv и __pycache__

**Проблема:** Multi-chat — AI повторяет код из предыдущего чата
- **Решение:** Убедитесь, что чат действительно новый (Command+Shift+L)
