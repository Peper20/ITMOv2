# Практика 04: Spec-driven разработка и расширение контекста

**Связь с лекцией:** Agents.md — управление AI через спецификации и расширенный контекст

## Цель семинара

- Создать "единственный источник правды" через файл `Agents.md` (спецификация проекта)
- Научиться использовать расширенный контекст для сложной разработки
- Мигрировать приложение с in-memory на SQLite через Spec-driven подход

## Ожидаемые результаты

Студенты создадут продакшен-версию WeatherService через Spec-driven разработку:
- Файл `Agents.md` с полной спецификацией проекта
- Миграция хранения данных из памяти в SQLite
- Рефакторинг на модульную архитектуру (routers, services, models)
- Интеграция с OpenWeatherMap API
- Журнал spec-driven разработки

---

## 1. Вступление (5 минут)

## 📋 Проект: "PythonNotify" (Интеграция)
Мы добавляем реальную погоду.
*   Сервис должен ходить в OpenWeatherMap API.
*   Сервис должен делать это асинхронно (не блокируя других пользователей).
*   Код должен быть разбит по папкам.

### Что говорит преподаватель
- «В Практике 3 мы управляли AI через отдельные промпты. Каждый раз объясняли контекст заново»
- «Сегодня создадим `Agents.md` — файл-спецификацию, который содержит ВСЮ информацию о проекте»
- «AI прочитает этот файл ОДИН раз и будет следовать спецификации во всех дальнейших задачах»

### Что показывать на экране
- Проблема: в Практике 3 приходилось повторять контекст в каждом промпте
- Решение: `Agents.md` как центральная спецификация
- Структура файла Agents.md

### Инструкции студентам
- Откройте проект из Практики 3
- Создайте файл `Agents.md` в корне проекта
- Откройте `task.py` для журнала

### Техники вовлечения
- Вопрос: «Сколько раз в Практике 3 вы повторяли "используй FastAPI"?»
- Опрос: «Кто забыл упомянуть важную деталь в промпте и получил неправильный код?»

---

## 2. Задание 1 — Создание Agents.md (25 минут)

### Цель блока
Написать полную спецификацию проекта в формате Agents.md

### Материалы
- Шаблон Agents.md
- Результаты из Практики 1-3

### Что говорит преподаватель
- «Agents.md — это договор между вами и AI. Здесь описано ВСЁ: архитектура, технологии, правила кода»
- «Структура: Project Overview → Tech Stack → Architecture → Development Rules → Current Tasks»
- «AI будет читать этот файл перед каждой задачей. Одна спецификация — тысячи задач»

### Что показывать на экране
- Пример структуры Agents.md
- Как @-упоминания работают в Cursor
- Разница: промпт с/без Agents.md

### Инструкции студентам
1. Создайте файл `Agents.md` в корне проекта
2. Скопируйте базовую структуру:

```markdown
# WeatherService - Спецификация проекта

## 📋 Project Overview
**Название:** WeatherService
**Описание:** REST API для подписки на уведомления о погоде
**Стадия:** MVP → Production-ready
**Цель:** Предоставить клиентским приложениям API для управления подписками на погоду

## 🛠 Tech Stack
**Backend:**
- Python 3.10+
- FastAPI (async web framework)
- Pydantic v2 (валидация данных)
- uvicorn (ASGI сервер)

**Database:**
- SQLite (основное хранилище)
- aiosqlite (async работа с SQLite)

**External APIs:**
- OpenWeatherMap API (данные о погоде)
- httpx (async HTTP клиент)

**Testing:**
- pytest
- pytest-asyncio

## 🏗 Architecture

### Модульная структура
```
app/
├── __init__.py
├── main.py              # FastAPI app initialization
├── models/
│   └── subscription.py  # Pydantic models
├── services/
│   ├── subscription_service.py  # Business logic
│   └── weather_service.py       # Weather API integration
├── routers/
│   └── subscriptions.py # API endpoints
└── database/
    └── db.py            # SQLite connection
```

### Принципы архитектуры
1. **Separation of Concerns**: Router → Service → Database
2. **Async First**: Все I/O операции асинхронные
3. **Dependency Injection**: FastAPI dependencies для сервисов

### API Endpoints
- `POST /subscribe` - создать подписку
- `GET /subscriptions` - получить все подписки
- `DELETE /subscribe/{email}` - удалить подписку
- `GET /weather/{city}` - получить погоду в городе

## 📐 Development Rules

### Code Style
- Type hints обязательны для всех функций
- Docstrings в Google Style
- snake_case для функций, PascalCase для классов
- Максимальная длина строки: 100 символов

### Error Handling
- Используй HTTPException для API ошибок
- Логируй все исключения
- Возвращай понятные сообщения об ошибках

### Database
- Используй async контекстные менеджеры
- Всегда закрывай соединения
- SQL-инъекции недопустимы (параметризованные запросы)

## 🎯 Current Tasks

### ✅ Completed (Practice 3)
- [x] Базовая структура FastAPI приложения
- [x] Pydantic модели
- [x] In-memory хранилище
- [x] POST /subscribe endpoint

### 🔄 In Progress (Practice 4)
- [ ] Миграция на SQLite
- [ ] Рефакторинг на модули (routers/services/models)
- [ ] Интеграция с OpenWeatherMap API
- [ ] Полное покрытие CRUD операций

### 📝 Implementation Notes
**Миграция на SQLite:**
1. Создать `database/db.py` с async connection pool
2. Создать таблицу `subscriptions` (id, city, email, created_at)
3. Переписать SubscriptionService для работы с SQLite
4. Обновить роутеры для использования нового сервиса

**Weather API Integration:**
- API Key хранить в `.env`
- Кэшировать результаты (in-memory на первом этапе)
- Обрабатывать ошибки API (404, 500, timeout)
```

3. **Адаптируйте под свой проект:** добавьте детали из ваших предыдущих артефактов
4. Сохраните файл

### Техники вовлечения
- Работа в парах: обменяйтесь Agents.md с соседом, найдите 1 недостающую деталь
- Чекпоинт на 15-й минуте: «У кого уже есть секция Architecture?»

### Ожидаемый артефакт
- Полный файл `Agents.md` с 5 основными секциями
- Спецификация содержит конкретные детали (не общие фразы)
- Описаны текущие задачи для миграции

---

## 3. Задание 2 — Spec-driven миграция на SQLite (30 минут)

### Цель блока
Использовать Agents.md для управления миграцией хранилища с in-memory на SQLite

### Материалы
- Созданный Agents.md
- Код из Практики 3

### Что говорит преподаватель
- «Теперь попросим AI сделать миграцию, ССЫЛАЯСЬ на Agents.md»
- «Промпт будет простой: "@Agents.md Выполни миграцию на SQLite согласно Implementation Notes"»
- «AI прочитает спецификацию и поймёт ВСЁ: структуру, правила, технологии»

### Что показывать на экране
- Как использовать @Agents.md в Cursor Chat
- Сравнение: промпт без спецификации vs с спецификацией
- Целевая структура с database/db.py

### Инструкции студентам

#### Шаг 1: Создать database layer (10 минут)
1. Откройте Cursor Chat (`Cmd+L` / `Ctrl+L`)
2. Напишите промпт:
   ```
   @Agents.md

   Создай app/database/db.py согласно спецификации.
   Требования:
   - Async connection pool для SQLite
   - Функция init_db() для создания таблицы subscriptions
   - Функция get_db() для получения connection
   - Следуй Development Rules из спецификации
   ```

3. Примените сгенерированный код
4. Запишите в журнал: что AI сделал правильно, опираясь на Agents.md?

#### Шаг 2: Рефакторинг SubscriptionService (10 минут)
1. Промпт:
   ```
   @Agents.md @app/services/subscription_service.py

   Перепиши SubscriptionService для работы с SQLite вместо in-memory.
   Используй async/await и aiosqlite согласно Tech Stack.
   Методы: create, get_all, delete_by_email.
   ```

2. Проверьте сгенерированный код:
   - Есть ли type hints?
   - Используется ли aiosqlite?
   - Обрабатываются ли ошибки?

#### Шаг 3: Обновить endpoints (10 минут)
1. Промпт:
   ```
   @Agents.md @app/routers/subscriptions.py

   Обнови endpoints для работы с новым SubscriptionService.
   Добавь endpoint GET /subscriptions (отсутствует).
   ```

2. Протестируйте через Swagger UI

### Техники вовлечения
- «Peer review»: покажите соседу сгенерированный код — соответствует ли он Agents.md?
- Вопрос: «Что AI сделал автоматически благодаря спецификации?»

### Ожидаемый артефакт
- Работающая миграция на SQLite
- Все endpoints работают с базой данных
- Код следует правилам из Agents.md (async, type hints, docstrings)

---

## 4. Задание 3 — Интеграция Weather API (25 минут)

### Цель блока
Добавить интеграцию с OpenWeatherMap через Spec-driven подход

### Что говорит преподаватель
- «Последний шаг — реальная погода из OpenWeatherMap»
- «Agents.md уже содержит раздел про Weather API Integration — AI знает, что делать»

### Инструкции студентам

#### Шаг 1: Получить API Key (5 минут)
1. Зарегистрируйтесь на https://openweathermap.org/
2. Получите бесплатный API Key
3. Создайте `.env` файл:
   ```
   OPENWEATHER_API_KEY=your_key_here
   ```

#### Шаг 2: Создать WeatherService (10 минут)
1. Промпт:
   ```
   @Agents.md

   Создай app/services/weather_service.py.
   Класс WeatherService с методом async get_weather(city: str).
   Используй httpx для запросов к OpenWeatherMap API.
   API URL: https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}

   Обработай ошибки:
   - 404: город не найден
   - 500: API недоступен
   - Timeout
   ```

2. Проверьте: есть ли async/await? Есть ли error handling?

#### Шаг 3: Интегрировать в endpoint (10 минут)
1. Промпт:
   ```
   @Agents.md @app/routers/subscriptions.py

   Обнови POST /subscribe:
   - При создании подписки проверяй существование города через WeatherService
   - Если город не существует — возвращай 404
   - В ответе включай текущую погоду
   ```

2. Протестируйте:
   ```bash
   curl -X POST http://localhost:8000/subscribe \
     -H "Content-Type: application/json" \
     -d '{"city": "London", "email": "test@example.com"}'
   ```

### Техники вовлечения
- Демо в реальном времени: кто-то показывает на экране запрос с реальной погодой
- Вопрос: «Сколько раз вам пришлось напомнить AI про async/httpx?»

### Ожидаемый артефакт
- Работающая интеграция с Weather API
- POST /subscribe возвращает реальную погоду
- Обработаны все граничные случаи (404, timeout)

---

## 5. Демонстрация: До/После Agents.md (5 минут)

### Что происходит
Сравнение двух подходов: Практика 3 (промпты) vs Практика 4 (Agents.md)

### Что говорит преподаватель
- «Практика 3: каждый промпт содержал 5-7 строк контекста»
- «Практика 4: промпт из 1 строки + @Agents.md — AI знает весь контекст»
- «Результат: меньше ошибок, больше консистентности»

### Что показывать на экране
Слайд с метриками:
| Метрика | Практика 3 (промпты) | Практика 4 (Agents.md) |
|---------|---------------------|----------------------|
| Средняя длина промпта | 120 символов | 30 символов |
| Повторение контекста | Каждый раз | Один раз |
| Ошибки из-за забытого контекста | ~30% | ~5% |
| Время на задачу | 100% | ~60% |

### Техники вовлечения
- Голосование: «Кто будет использовать Agents.md в своих проектах?»

---

## 6. Домашнее задание

### Обязательное (8 баллов)

#### 1. Расширение Agents.md (3 балла)
Добавьте в Agents.md новые секции:

**Testing Strategy:**
```markdown
## 🧪 Testing Strategy

### Test Pyramid
- Unit: 60% (сервисы, утилиты)
- Integration: 30% (БД, внешние API)
- E2E: 10% (полные флоу через API)

### Coverage Requirements
- Минимум 80% покрытие кода
- 100% покрытие критических путей (подписка, валидация)

### Test Naming Convention
`test_<функция>_<сценарий>_<ожидаемый_результат>`
Пример: `test_create_subscription_valid_city_returns_200`
```

**Deployment:**
```markdown
## 🚀 Deployment

### Environment Variables
- `DATABASE_URL`: путь к SQLite файлу
- `OPENWEATHER_API_KEY`: ключ API
- `LOG_LEVEL`: уровень логирования (DEBUG/INFO/ERROR)

### Docker
- Base image: python:3.10-slim
- Expose port: 8000
- Health check: GET /health
```

#### 2. Spec-driven тестирование (5 баллов)
Используя обновлённый Agents.md, попросите AI:

1. Создать `tests/test_subscription_service.py`:
   ```
   @Agents.md

   Создай unit-тесты для SubscriptionService согласно Testing Strategy.
   Покрой все методы: create, get_all, delete_by_email.
   Используй pytest-asyncio и fixtures.
   ```

2. Создать `tests/test_weather_service.py`:
   ```
   @Agents.md

   Создай unit-тесты для WeatherService.
   Mock httpx запросы. Тест-кейсы:
   - Успешный запрос
   - 404 (город не найден)
   - Timeout
   ```

3. Запустите тесты: `pytest tests/ -v --cov=app`

**Требования:**
- Минимум 10 тест-кейсов
- Покрытие > 70%
- Все тесты проходят

### Со звёздочкой (*) (4 балла)

#### 1. CI/CD через Agents.md (2 балла)
Добавьте в Agents.md секцию CI/CD и попросите AI создать `.github/workflows/test.yml`:

```
@Agents.md

Создай GitHub Actions workflow для автоматического тестирования.
Триггер: push и pull_request в main.
Шаги: setup python → install deps → run tests → upload coverage.
```

#### 2. Telegram бот как клиент API (2 балла)
Создайте отдельный проект `telegram-bot/`:

1. Обновите Agents.md с новой секцией:
```markdown
## 📱 Telegram Bot Integration (Optional)

**Назначение:** Telegram бот как клиент WeatherService API
**Архитектура:** Бот → REST API (а не прямо к БД)

**Endpoints usage:**
- /start → GET /health
- /subscribe {city} → POST /subscribe
- /weather → GET /weather/{city}
```

2. Попросите AI создать бота:
```
@Agents.md

Создай Telegram бота используя aiogram.
Бот должен вызывать REST API WeatherService (не базу данных!).
Команды: /start, /subscribe, /weather.
```

### Критерии оценки

| Критерий | Баллы | Что проверяется |
|:---|:---:|:---|
| **Agents.md** | 3 | Полнота спецификации, новые секции (Testing, Deployment) |
| **Миграция SQLite** | 3 | Работает ли БД, async правильно используется |
| **Weather API** | 2 | Реальная погода возвращается, errors handled |
| **Тесты (ДЗ)** | 5 | Покрытие, качество тестов |
| **CI/CD (★)** | 2 | Работает ли GitHub Actions |
| **Telegram (★)** | 2 | Бот использует API, а не БД напрямую |
| **Всего** | **12** (+4) | |

---

## 📚 Ключевые выводы

### Что студенты узнали:
1. **Agents.md > множество промптов**: одна спецификация лучше сотни повторений
2. **Spec-driven development**: спецификация → задачи → реализация
3. **Контекст решает всё**: @-упоминания + спецификация = точный результат

### Эволюция подхода:
- **Практика 1**: AI генерирует артефакты планирования
- **Практика 2**: R.C.T.F. — структурированные промпты
- **Практика 3**: P.M.A. — управление AI-агентом в IDE
- **Практика 4**: Spec-driven — AI работает по спецификации проекта

### Следующие шаги:
- **Практика 5**: Оркестрация задач через AI workflows
- **Практика 6**: CI/CD с AI-агентами
- Студенты готовы к production-разработке с AI!

---

**Важно:** Сохраните ваш `Agents.md` — это ваша документация, которая работает как код! 📝
