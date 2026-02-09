# Тестирование: Практика 4 - MCP + Интеграция с Weather API

## 🧪 Обзор тестирования

Этот документ описывает стратегию тестирования для практики 4, охватывающую unit-тесты, интеграционные тесты и тесты API. Мы сосредоточимся на проверке интеграции с OpenWeatherMap API, обработке ошибок и соблюдении Model Context Protocol.

## 📋 Типы тестов

### Unit-тесты
- **Цель:** Проверить отдельные компоненты изолированно
- **Область:** Сервисы, модели, утилиты
- **Инструменты:** pytest, unittest.mock

### Интеграционные тесты
- **Цель:** Проверить взаимодействие между компонентами
- **Область:** Сервисы + внешние API, роутеры + сервисы
- **Инструменты:** pytest, httpx для моков API

### API тесты
- **Цель:** Проверить эндпоинты FastAPI
- **Область:** Все роутеры и модели ответов
- **Инструменты:** pytest, TestClient из FastAPI

## 🏗️ Структура тестов

```
tests/
├── __init__.py
├── conftest.py           # Фикстуры pytest
├── test_models.py        # Тесты моделей Pydantic
├── test_services/        # Тесты сервисов
│   ├── __init__.py
│   ├── test_weather.py   # Тесты сервиса погоды
│   └── test_subscription.py # Тесты сервиса подписок
└── test_routers/         # Тесты роутеров
    ├── __init__.py
    ├── test_weather.py   # Тесты эндпоинтов погоды
    └── test_subscriptions.py # Тесты эндпоинтов подписок
```

## 🧩 Unit-тесты

### Тесты моделей (test_models.py)
```python
def test_weather_response_validation():
    """Тест валидации модели ответа погоды"""
    # Позитивный тест: корректные данные
    valid_data = {
        "city": "Moscow",
        "temperature": 15.5,
        "description": "ясно",
        "humidity": 65
    }
    weather = WeatherResponse(**valid_data)
    assert weather.city == "Moscow"
    
    # Негативный тест: неверные данные
    with pytest.raises(ValidationError):
        WeatherResponse(city="", temperature="не число")
```

### Тесты сервисов (test_services/test_weather.py)
```python
@pytest.mark.asyncio
async def test_get_weather_success(mock_weather_api):
    """Тест успешного получения данных о погоде"""
    # Настройка мока API
    mock_weather_api.return_value = {
        "main": {"temp": 15.5},
        "weather": [{"description": "ясно"}],
        "main": {"humidity": 65}
    }
    
    service = WeatherService()
    result = await service.get_weather("Moscow")
    
    assert result.city == "Moscow"
    assert result.temperature == 15.5
    assert result.description == "ясно"
```

## 🔗 Интеграционные тесты

### Тесты сервисов с моками API
```python
@pytest.mark.asyncio
async def test_weather_service_error_handling(mock_weather_api_error):
    """Тест обработки ошибок API"""
    mock_weather_api_error.side_effect = HTTPError("API недоступен")
    
    service = WeatherService()
    result = await service.get_weather("InvalidCity")
    
    assert result is None
    # Или проверка специального ответа об ошибке
```

### Тесты роутеров (test_routers/test_weather.py)
```python
def test_weather_endpoint_success(test_client):
    """Тест эндпоинта погоды"""
    response = test_client.get("/weather/Moscow")
    assert response.status_code == 200
    data = response.json()
    assert "city" in data
    assert "temperature" in data
    assert "description" in data
```

## 🌐 API тесты

### Полное тестирование эндпоинтов
```python
def test_subscription_workflow(test_client):
    """Полный тест workflow подписки"""
    # Создание подписки
    response = test_client.post("/subscriptions", json={"city": "Moscow"})
    assert response.status_code == 201
    
    # Получение всех подписок
    response = test_client.get("/subscriptions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # Удаление подписки
    response = test_client.delete("/subscriptions/Moscow")
    assert response.status_code == 200
```

## 🐛 Тестирование ошибок и граничных случаев

### Ошибки API
```python
@pytest.mark.asyncio
async def test_weather_api_404_error(mock_weather_api_404):
    """Тест обработки 404 ошибки (город не найден)"""
    mock_weather_api_404.return_value = None  # Или специальный ответ ошибки
    
    service = WeatherService()
    result = await service.get_weather("NonExistentCity")
    
    assert result is None
    # Или проверка специального сообщения об ошибке
```

### Граничные значения
```python
def test_temperature_boundaries():
    """Тест граничных значений температуры"""
    # Крайние значения температуры
    extreme_data = {
        "city": "Yakutsk",
        "temperature": -50.0,  # Очень холодно
        "description": "ясно",
        "humidity": 80
    }
    
    weather = WeatherResponse(**extreme_data)
    assert weather.temperature == -50.0
```

## ⚡ Тесты производительности

### Тесты ограничения частоты запросов
```python
@pytest.mark.asyncio
async def test_rate_limiting():
    """Тест ограничения частоты запросов"""
    service = WeatherService()
    
    # Множественные быстрые запросы
    tasks = [service.get_weather("Moscow") for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Проверка, что не все запросы прошли успешно
    successful = [r for r in results if r is not None]
    assert len(successful) <= 5  # Предполагаемый лимит
```

## 🔧 Настройка тестовой среды

### conftest.py
```python
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def test_client():
    """Фикстура тестового клиента FastAPI"""
    return TestClient(app)

@pytest.fixture
def mock_weather_api():
    """Фикстура мока API погоды"""
    with patch('app.services.weather.httpx.AsyncClient.get') as mock:
        yield mock

@pytest.fixture
def mock_weather_api_error():
    """Фикстура мока ошибки API"""
    with patch('app.services.weather.httpx.AsyncClient.get') as mock:
        mock.side_effect = HTTPError("API ошибка")
        yield mock
```

## 📊 Покрытие тестами

### Целевое покрытие
- **Unit-тесты:** 80%+ покрытия сервисов и моделей
- **Интеграционные тесты:** Все основные workflow
- **API тесты:** Все публичные эндпоинты

### Запуск тестов
```bash
# Все тесты
pytest tests/ -v

# Только unit-тесты
pytest tests/test_models.py tests/test_services/ -v

# Только API тесты
pytest tests/test_routers/ -v

# С покрытием кода
pytest tests/ --cov=app --cov-report=html
```

## 🚨 Тестирование безопасности

### Валидация входных данных
```python
def test_sql_injection_prevention():
    """Тест защиты от SQL инъекций"""
    # Попытка инъекции в параметр города
    malicious_city = "Moscow'; DROP TABLE subscriptions; --"
    response = test_client.get(f"/weather/{malicious_city}")
    
    # Должна быть корректная обработка или ошибка валидации
    assert response.status_code != 500  # Не должно быть серверной ошибки
```

### Валидация API ключей
```python
def test_invalid_api_key_handling():
    """Тест обработки неверного API ключа"""
    # Сохранение оригинального ключа
    original_key = os.getenv('OPENWEATHER_API_KEY')
    
    # Установка неверного ключа
    os.environ['OPENWEATHER_API_KEY'] = 'invalid_key'
    
    # Тест должен корректно обрабатывать ошибку аутентификации
    response = test_client.get("/weather/Moscow")
    assert response.status_code in [401, 503]  # Ожидаемые коды ошибок
    
    # Восстановление оригинального ключа
    os.environ['OPENWEATHER_API_KEY'] = original_key
```

## 📝 Чек-лист тестирования

Перед сдачей убедитесь, что:

### Unit-тесты
- [ ] Все сервисы имеют базовые unit-тесты
- [ ] Модели Pydantic проверяют валидацию данных
- [ ] Обработка ошибок тестируется изолированно
- [ ] Моки корректно имитируют внешние зависимости

### Интеграционные тесты
- [ ] Основные workflow покрыты (подписка → получение погоды)
- [ ] Интеграция с внешними API тестируется с моками
- [ ] Обработка сетевых ошибок проверена

### API тесты
- [ ] Все эндпоинты возвращают ожидаемые HTTP коды
- [ ] Модели ответов соответствуют документации
- [ ] Ошибки валидации обрабатываются корректно

### Производительность и безопасность
- [ ] Ограничение частоты запросов работает корректно
- [ ] Входные данные валидируются и санитизируются
- [ ] Нет уязвимостей инъекций

## 🔍 Отладка тестов

### Распространенные проблемы
```python
# Проблема: Асинхронные тесты не работают
# Решение: Используйте @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result

# Проблема: Моки не работают правильно
# Решение: Убедитесь в правильности пути импорта
with patch('app.services.weather.httpx.AsyncClient.get') as mock:
    mock.return_value = mock_response
```

### Логирование тестов
```python
import logging

def test_with_logging(caplog):
    """Тест с логированием для отладки"""
    caplog.set_level(logging.INFO)
    
    # Выполнение теста
    result = some_function()
    
    # Проверка логов
    assert "ожидаемое сообщение" in caplog.text
```

Этот документ должен служить полным руководством по тестированию вашего приложения. Регулярно запускайте тесты во время разработки для быстрого выявления проблем.