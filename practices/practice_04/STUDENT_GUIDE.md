# Руководство для студентов: Практика 4 - Spec-driven разработка с Agents.md

## 🎯 Пошаговые инструкции

### Шаг 1: Подготовка Agents.md (15 минут)

**1.1 Проверка Agents.md из Практики 3**
- Откройте файл `Agents.md` из домашнего задания Практики 3
- Убедитесь, что все секции заполнены:
  - Project Overview
  - Tech Stack
  - Architecture
  - Development Rules
  - Current Tasks

**1.2 Понимание структуры Agents.md**
```markdown
# WeatherService - Спецификация проекта

## 📋 Project Overview
Краткое описание проекта, целевой аудитории

## 🛠 Tech Stack
Список технологий: FastAPI, SQLite, Pydantic v2, OpenWeatherMap API

## 🏗 Architecture
Компоненты системы и их взаимодействие

## 📐 Development Rules
Правила разработки: Code Style, Naming, Error Handling

## 🎯 Current Tasks
Список текущих задач для реализации
```

**1.3 Обновление Current Tasks**
Добавьте в секцию `Current Tasks` задачи Практики 4:
```markdown
## 🎯 Current Tasks
1. [ ] Миграция с in-memory на SQLite
2. [ ] Интеграция с OpenWeatherMap API
3. [ ] Добавление эндпоинта GET /weather/{city}
4. [ ] Кэширование запросов к API (опционально)
```

### Шаг 2: Spec-driven подход — правило @Agents.md (10 минут)

**2.1 Что такое Spec-driven разработка?**
- Единый источник правды для всего проекта
- Все промпты начинаются с `@Agents.md`
- AI видит полный контекст: архитектуру, правила, задачи
- Консистентность кода гарантирована

**2.2 Правило использования @Agents.md**
Каждый промпт в Cursor Chat должен начинаться с:
```
@Agents.md [ваша задача]
```

**Пример:**
```
@Agents.md Создай файл database.py с async функциями для работы с SQLite:
- create_table() — создание таблицы subscriptions
- insert_subscription() — добавление подписки
- get_all_subscriptions() — получение всех подписок
- delete_subscription() — удаление по city
```

**2.3 Почему это работает лучше?**
- БЕЗ @Agents.md: AI не знает про ваши правила → генерирует несовместимый код
- С @Agents.md: AI видит весь контекст → генерирует код в едином стиле

### Шаг 3: Миграция на SQLite (30 минут)

**3.1 Создание database.py через @Agents.md**

1. Создайте новый чат в Cursor (Command+Shift+L)
2. Промпт:
```
@Agents.md Создай файл database.py для работы с SQLite (aiosqlite):

Требования:
- Async функции для всех операций
- Таблица subscriptions: (id INTEGER PRIMARY KEY, city TEXT, email TEXT, created_at TEXT)
- Функции:
  * init_db() — создание таблицы
  * create_subscription(city, email)
  * get_all_subscriptions() → List[dict]
  * delete_subscription_by_city(city)
  * subscription_exists(city) → bool

Используй context manager для async with aiosqlite.connect()
```

3. Примените сгенерированный код
4. **Запишите промпт в `task.py` → `SPEC_DRIVEN_LOGS`**

**3.2 Обновление main.py для использования database.py**

1. Новый чат
2. Промпт:
```
@Agents.md @main.py @database.py Обнови main.py:

1. Импортируй функции из database.py
2. Добавь startup event для инициализации БД:
   @app.on_event("startup")
   async def startup():
       await init_db()
3. Замени глобальный список subscriptions на вызовы database функций
```

3. Примените код
4. Запишите в `SPEC_DRIVEN_LOGS`

**3.3 Тестирование миграции**
```bash
# Запустите сервер
uvicorn main:app --reload

# Проверьте, что создался файл subscriptions.db
ls subscriptions.db

# Протестируйте эндпоинты
curl -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"city": "Moscow", "email": "test@example.com"}'

curl http://localhost:8000/subscriptions
```

### Шаг 4: Интеграция с OpenWeatherMap API (30 минут)

**4.1 Получение API ключа**
- Перейдите на [OpenWeatherMap](https://openweathermap.org/api)
- Зарегистрируйтесь и получите бесплатный API ключ
- Скопируйте ключ для следующего шага

**4.2 Создание weather_service.py через @Agents.md**

1. Новый чат
2. Промпт:
```
@Agents.md Создай файл weather_service.py для интеграции с OpenWeatherMap:

Требования:
- Класс WeatherService с методом get_weather(city: str)
- Используй httpx для async HTTP запросов
- API endpoint: https://api.openweathermap.org/data/2.5/weather
- Параметры: ?q={city}&appid={API_KEY}&units=metric
- Обработка ошибок:
  * 404 → город не найден (raise HTTPException 404)
  * 5xx → сервис недоступен (raise HTTPException 503)
  * Timeout → raise HTTPException 504
- Возвращаемая модель: WeatherData (city, temperature, description, humidity)

Добавь простое кэширование: dict с TTL 10 минут (опционально)
```

3. Примените код
4. Запишите в `SPEC_DRIVEN_LOGS`

**4.3 Создание Pydantic модели WeatherData**

1. Промпт:
```
@Agents.md @models.py Добавь в models.py Pydantic модель WeatherData:

Поля:
- city: str
- temperature: float
- description: str
- humidity: int
- timestamp: datetime (default: datetime.now())

Используй Pydantic v2 синтаксис
```

**4.4 Добавление эндпоинта GET /weather/{city}**

1. Промпт:
```
@Agents.md @main.py @weather_service.py @models.py Добавь эндпоинт GET /weather/{city}:

- Принимает city как path parameter
- Создает экземпляр WeatherService (передай API_KEY из переменной окружения)
- Вызывает get_weather(city)
- Возвращает WeatherData response_model
- Обрабатывает HTTPException из WeatherService

Добавь docstring с примером запроса
```

2. Примените код
3. Запишите в `SPEC_DRIVEN_LOGS`

**4.5 Настройка переменных окружения**

Создайте файл `.env`:
```
OPENWEATHER_API_KEY=your_actual_api_key_here
```

Обновите `main.py` для загрузки env:
```python
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
```

**4.6 Тестирование интеграции**
```bash
# Установите python-dotenv и httpx
pip install python-dotenv httpx

# Перезапустите сервер
uvicorn main:app --reload

# Протестируйте эндпоинт
curl http://localhost:8000/weather/Moscow
curl http://localhost:8000/weather/London
curl http://localhost:8000/weather/Narnia  # Должен вернуть 404
```

### Шаг 5: Обновление Agents.md после изменений (10 минут)

**5.1 Spec-driven workflow: обновление спецификации**

После каждого изменения кода обновляйте `Agents.md`:

1. Промпт:
```
@Agents.md @database.py @weather_service.py @models.py Обнови секцию Architecture в Agents.md:

Добавь новые компоненты:
4. Database Layer (database.py):
   - SQLite async operations
   - CRUD для subscriptions

5. Weather API Integration (weather_service.py):
   - OpenWeatherMap client
   - Caching layer (опционально)

Обнови Tech Stack: добавь aiosqlite, httpx, python-dotenv
```

2. Примените изменения в Agents.md
3. **Важно:** Agents.md всегда должен отражать текущее состояние проекта

**5.2 Обновление Current Tasks**

Отметьте выполненные задачи:
```markdown
## 🎯 Current Tasks
1. [x] Миграция с in-memory на SQLite
2. [x] Интеграция с OpenWeatherMap API
3. [x] Добавление эндпоинта GET /weather/{city}
4. [ ] Кэширование запросов к API (опционально)
5. [ ] Добавление rate limiting (домашнее задание)
```

### Шаг 6: Тестирование и документация (5 минут)

**6.1 Автоматическая документация Swagger UI**
- Откройте http://localhost:8000/docs
- Протестируйте все эндпоинты через интерфейс
- Сделайте скриншот для отчета

**6.2 Ручное тестирование**
```bash
# Полный flow
curl -X POST http://localhost:8000/subscribe -H "Content-Type: application/json" \
  -d '{"city": "Moscow", "email": "user@test.com"}'

curl http://localhost:8000/weather/Moscow

curl http://localhost:8000/subscriptions

curl -X DELETE http://localhost:8000/subscribe/Moscow
```

**6.3 Проверка базы данных**
```bash
# Откройте SQLite DB
sqlite3 subscriptions.db

# SQL queries
SELECT * FROM subscriptions;
.exit
```

## 🐛 Распространенные проблемы и решения

**Проблема: API ключ не работает**
- Решение: Проверьте `.env` файл и убедитесь, что load_dotenv() вызывается
- Решение: Проверьте активацию ключа в аккаунте OpenWeatherMap (может занять до 2 часов)

**Проблема: Ошибки импорта aiosqlite**
- Решение: `pip install aiosqlite`

**Проблема: AI не применяет правила из Agents.md**
- Решение: Убедитесь, что каждый промпт начинается с `@Agents.md`
- Решение: Проверьте, что Agents.md находится в корне проекта

**Проблема: Контекст слишком большой (token limit)**
- Решение: Используйте отдельные чаты для каждой подзадачи
- Решение: Указывайте только релевантные файлы (@database.py вместо @codebase)

**Проблема: AI генерирует код в другом стиле**
- Решение: Явно укажите `@Agents.md` в начале промпта
- Решение: Обновите секцию Development Rules в Agents.md

## 📝 Руководство по реализации домашнего задания

### Обязательное домашнее задание

**1. Rate Limiting для Weather API (3 балла)**
- Ограничение: 60 запросов в минуту (бесплатный тариф OpenWeatherMap)
- Реализуйте в классе `WeatherService`
- Используйте декоратор или middleware
- Промпт:
  ```
  @Agents.md @weather_service.py Добавь rate limiting:
  - Ограничь до 60 запросов/минуту
  - Если превышен лимит: raise HTTPException 429 "Too Many Requests"
  - Используй простой счетчик с таймстампами (без внешних библиотек)
  ```

**2. Unit-тесты для WeatherService (3 балла)**
- Создайте `tests/test_weather_service.py`
- Используйте pytest + pytest-asyncio
- Мокайте httpx запросы
- Промпт:
  ```
  @Agents.md Создай tests/test_weather_service.py:
  - Мокай httpx.AsyncClient для изоляции тестов
  - Тесты:
    * test_get_weather_success() — успешный запрос
    * test_get_weather_city_not_found() — 404 ошибка
    * test_get_weather_service_unavailable() — 5xx ошибка
  - Используй pytest-asyncio для async тестов
  ```

**3. Простой HTML фронтенд (4 балла)**
- Создайте `static/index.html` с JavaScript
- Функции: подписка, просмотр подписок, получение погоды
- Промпт:
  ```
  @Agents.md Создай static/index.html:
  - Форма подписки (city, email)
  - Список текущих подписок
  - Кнопка "Get Weather" для каждой подписки
  - Отображение погоды (temperature, description, humidity)
  - Используй Fetch API для запросов к /subscribe, /subscriptions, /weather/{city}
  - Простой CSS для читаемости
  ```

### Бонусные задачи

**1. WebSocket real-time уведомления (+ 2 балла)**
- Создайте WebSocket эндпоинт `/ws`
- Отправляйте обновления погоды каждые 5 минут для всех подписок
- Промпт:
  ```
  @Agents.md Добавь WebSocket support в main.py:
  - Эндпоинт /ws
  - Каждые 5 минут: получай погоду для всех подписанных городов
  - Отправляй JSON с обновлениями через WebSocket
  - Используй asyncio.create_task для фоновой задачи
  ```

**2. Docker деплой (+ 2 балла)**
- Создайте `Dockerfile` и `docker-compose.yml`
- Промпт:
  ```
  @Agents.md Создай Dockerfile для FastAPI приложения:
  - Base image: python:3.11-slim
  - WORKDIR /app
  - Копируй requirements.txt и устанавливай зависимости
  - Копируй код приложения
  - CMD: uvicorn main:app --host 0.0.0.0 --port 8000

  Создай docker-compose.yml:
  - Сервис app с Dockerfile
  - Volume для subscriptions.db
  - Переменные окружения из .env
  ```

**3. Кэширование с TTL (+ 1 балл)**
- Реализуйте кэширование погоды с TTL 10 минут
- Используйте простой dict или cachetools
- Промпт:
  ```
  @Agents.md @weather_service.py Добавь кэширование в get_weather():
  - Ключ кэша: city
  - TTL: 10 минут
  - Структура: {"city": {"data": {...}, "timestamp": ...}}
  - При повторном запросе: проверяй timestamp, если < 10 мин → return из кэша
  ```

## 🔍 Чек-лист код-ревью

Перед сдачей убедитесь:
- [ ] Все промпты записаны в `task.py` → `SPEC_DRIVEN_LOGS`
- [ ] `Agents.md` обновлен и отражает текущую архитектуру
- [ ] Все эндпоинты работают (проверено через Swagger UI)
- [ ] SQLite база данных создается автоматически при запуске
- [ ] Weather API интеграция работает с вашим API ключом
- [ ] Код следует правилам из `Agents.md` (async, type hints, HTTPException)
- [ ] `.env` файл не закоммичен в git (добавлен в .gitignore)

## 🎓 Результаты обучения

После завершения этой практики вы должны понимать:
- Как использовать Agents.md как единый источник правды
- Spec-driven подход: спецификация → код (а не наоборот)
- Асинхронная работа с SQLite (aiosqlite)
- Интеграция с внешними API (httpx + async/await)
- Обработка ошибок в async контексте
- Преимущества @Agents.md для консистентности кода

## 📊 Сравнение с Практикой 3

| Аспект | Практика 3 (Cursor mechanics) | Практика 4 (Spec-driven) |
|:---|:---|:---|
| **Контекст** | @file, @codebase для каждого промпта | @Agents.md содержит весь контекст |
| **Правила** | .cursorrules (может не применяться) | Agents.md (всегда в контексте) |
| **Консистентность** | Нужно вручную следить | Гарантирована через спецификацию |
| **Архитектура** | Эволюционирует во время кодинга | Задается ДО кодинга в Agents.md |
| **Обновления** | N/A | Agents.md обновляется после каждого изменения |

## 📞 Ресурсы поддержки

- Документация OpenWeatherMap API: https://openweathermap.org/api
- Документация FastAPI: https://fastapi.tiangolo.com/
- aiosqlite: https://github.com/omnilib/aiosqlite
- httpx async: https://www.python-httpx.org/async/
- Pydantic v2: https://docs.pydantic.dev/latest/

Не забудьте задокументировать ваш процесс в `task.py` (SPEC_DRIVEN_LOGS, REFLECTION) и включите любые проблемы, с которыми столкнулись, и как решили через @Agents.md промпты.
