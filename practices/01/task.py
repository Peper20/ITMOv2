import json
import os
from typing import List, Dict, Optional

"""
ПРАКТИКА 1: ПЛАНИРОВАНИЕ РАЗРАБОТКИ С ИСПОЛЬЗОВАНИЕМ AI
Курс: AI-инструменты в жизни инженера (ИТМО)
Проект: "PythonNotify" - Веб-сервис для уведомлений о погоде (REST API)

ИНСТРУКЦИЯ:
1. Заполните секции, отмеченные "TODO".
2. Записывайте все ваши промпты в список PROMPT_LOGS.
3. Запускайте этот файл для проверки прогресса и генерации отчета.
"""

# =================================================================================================
# 1. ИНФОРМАЦИЯ О СТУДЕНТЕ И ГРУППЕ
# =================================================================================================
STUDENT_INFO = {
    "full_name": "TODO: Фамилия Имя (Лидера группы или индивидуально)",
    "group_number": "TODO: Номер группы",  
    "members": "TODO: Список участников (если работаете в команде)",
    "date": "TODO: YYYY-MM-DD"
}

# =================================================================================================
# 2. ЖУРНАЛ РАБОТЫ С AI (PROMPT LOG)
# =================================================================================================
class PromptLog:
    def __init__(self, task_id: str, prompt: str, model: str, result_summary: str, refinement: str = ""):
        self.task_id = task_id
        self.prompt = prompt
        self.model = model
        self.result_summary = result_summary
        self.refinement = refinement

    def to_dict(self):
        return self.__dict__

PROMPT_LOGS: List[PromptLog] = [
    # TODO: Добавьте сюда ваши промпты по мере выполнения заданий.
    # Пример:
    # PromptLog(
    #     task_id="1.1 User Stories", 
    #     prompt="Привет! Мы делаем сервис уведомлений о погоде...", 
    #     model="ChatGPT-4",
    #     result_summary="Сгенерировал 5 User Stories для API эндпоинтов.",
    #     refinement="Попросил уточнить типы клиентов API (веб/мобильные приложения)."
    # ),
]

# =================================================================================================
# 3. РЕЗУЛЬТАТЫ (АРТЕФАКТЫ)
# =================================================================================================

# Задание 1 (часть 1): Лёгкий event storming (события/акторы/команды)
EVENT_STORMING = """
TODO: Вставьте результат от AI.

Подсказка по формату:
## Actors
- ...

## Commands
- ...

## Domain Events
- ...
"""

# Задание 1 (часть 2): CJM (Customer Journey Map) / основной пользовательский путь
CJM = """
TODO: Вставьте CJM (6–8 шагов).
"""

# Задание 1 (часть 3): Roadmap по версиям (v1.0/v1.1/v2.0)
ROADMAP = """
TODO: Вставьте roadmap по версиям (слайс по ценности).
"""

# Задание 1 (часть 4): Epics
EPICS = """
TODO: Вставьте список Epics (4–6 штук).
"""

# Задание 1.1: User Stories
# Вставьте сюда финальный список User Stories для REST API
USER_STORIES = """
TODO: Вставьте результат от AI
1. Как пользователь веб-приложения, я хочу подписаться на погоду через POST /subscribe...
2. Как пользователь, я хочу получить текущую погоду через GET /weather/{city}...
"""

# Задание 1.2: Definition of Ready (DoR)
DEFINITION_OF_READY = """
TODO: Вставьте чек-лист DoR
"""

# Задание 2 (часть 1): Компоненты системы
ARCHITECTURE_COMPONENTS = """
TODO: Список компонентов
1. FastAPI Backend (REST API)
2. PostgreSQL Database (подписки пользователей)
3. OpenWeatherMap API (данные о погоде)
4. Client Apps (веб/мобильные приложения)
"""

# Задание 2 (часть 2): ADR (Architecture Decision Record)
ADR = """
TODO: Вставьте ADR.

Рекомендуемый шаблон:
## Контекст
...
## Решение
...
## Альтернативы
...
## Последствия / Trade-offs
...
"""

# Задание 2 (часть 3): Mermaid код (архитектурная схема REST API сервиса)
MERMAID_CODE = """
TODO: Код диаграммы (```mermaid ... ```)
Должна включать: Client → FastAPI Backend → PostgreSQL DB → Weather API
"""

# Опционально: ссылка/путь на изображение схемы (если сохраняли PNG в репозиторий)
MERMAID_IMAGE_URL = """
TODO: Вставьте ссылку или относительный путь, например:
- ./artifacts/board/architecture.png
- ссылка на доску Miro/Excalidraw
"""

# Задание 3 (часть 1): Definition of Done (DoD)
DEFINITION_OF_DONE = """
TODO: Вставьте чек-лист DoD
"""

# Задание 3 (часть 2): План тестирования (позитивные + негативные сценарии)
TEST_PLAN = """
TODO: Тест-кейсы
"""

# Задание 3 (часть 3): Functional Delivery (нарезка задач «по функции» в стиле Jira-тикетов)
FUNCTIONAL_DELIVERY = """
TODO: Вставьте список Jira-тикетов (6–10 штук) по v1.0.

Формат (рекомендуется):
1) Title:
   Description:
   Acceptance Criteria:
   Test cases:
   Dependencies/Notes:
"""

# Домашнее задание (обязательно): LLD по одному Epic
HOMEWORK_LLD = """
TODO: Выберите один Epic и сделайте LLD.

Допустимые форматы:
- Markdown (описание модулей/эндпоинтов/контрактов)
- схема (Mermaid/Draw.io) + пояснение
"""

# Домашнее задание (обязательно): улучшить DoR/DoD до версии 2.0
HOMEWORK_DOR_V2 = """
TODO: Улучшите DoR до версии 2.0 (что добавили и почему).
"""

HOMEWORK_DOD_V2 = """
TODO: Улучшите DoD до версии 2.0 (что добавили и почему).
"""

# Со звёздочкой (*): Edge Cases (если хотите дополнительно потренироваться в QA-мышлении)
EDGE_CASES = """
TODO: (Опционально) 10 граничных случаев для v1.0/v1.1.
"""

# =================================================================================================
# 4. РЕФЛЕКСИЯ
# =================================================================================================
REFLECTION = {
    "key_takeaway": """
    TODO: Главный инсайт практики.
    """,
    
    "tool_critique": """
    TODO: Что AI сделал плохо? Где он ошибся в планировании?
    """,
    
    "time_saved_estimate": "TODO: Оценка времени (например, 'Сэкономил 1 час')",
}

# =================================================================================================
# ЭКСПОРТ (НЕ МЕНЯЙТЕ КОД НИЖЕ)
# =================================================================================================
def export_report():
    if "TODO" in STUDENT_INFO["full_name"]:
        print("❌ ОШИБКА: Заполните секцию 1 (Информация о студенте)")
        return

    report = f"# Отчет по Практике 1: {STUDENT_INFO['full_name']}\n\n"
    report += f"**Группа:** {STUDENT_INFO['group_number']}\n"
    report += f"**Участники:** {STUDENT_INFO['members']}\n"
    report += f"**Дата:** {STUDENT_INFO['date']}\n\n"
    
    report += "## 1. Бизнес-артефакты и планирование\n\n"
    report += "### Event storming (light)\n" + EVENT_STORMING + "\n\n"
    report += "### CJM\n" + CJM + "\n\n"
    report += "### Roadmap\n" + ROADMAP + "\n\n"
    report += "### Epics\n" + EPICS + "\n\n"
    report += "### User Stories\n" + USER_STORIES + "\n\n"
    report += "### Definition of Ready (DoR)\n" + DEFINITION_OF_READY + "\n\n"
    
    report += "## 2. Архитектура\n\n"
    report += "### Компоненты\n" + ARCHITECTURE_COMPONENTS + "\n\n"
    report += "### ADR\n" + ADR + "\n\n"
    report += "### Mermaid\n```mermaid\n" + MERMAID_CODE + "\n```\n\n"
    report += "### Ссылка на схему\n" + MERMAID_IMAGE_URL + "\n\n"
    
    report += "## 3. Качество\n\n"
    report += "### Definition of Done\n" + DEFINITION_OF_DONE + "\n\n"
    report += "### План тестирования\n" + TEST_PLAN + "\n\n"
    report += "### Functional Delivery (Jira-тикеты)\n" + FUNCTIONAL_DELIVERY + "\n\n"

    report += "## 4. Домашнее задание\n\n"
    report += "### LLD по Epic\n" + HOMEWORK_LLD + "\n\n"
    report += "### DoR v2.0\n" + HOMEWORK_DOR_V2 + "\n\n"
    report += "### DoD v2.0\n" + HOMEWORK_DOD_V2 + "\n\n"
    report += "### Edge Cases (*)\n" + EDGE_CASES + "\n\n"

    report += "## 5. Журнал промптов\n\n"
    for log in PROMPT_LOGS:
        report += f"**Задача:** {log.task_id} ({log.model})\n"
        report += f"> {log.prompt}\n\n"
        report += f"*Результат:* {log.result_summary}\n"
        if log.refinement:
            report += f"*Улучшение:* {log.refinement}\n"
        report += "---\n"

    report += "\n## 6. Рефлексия\n\n"
    report += f"**Инсайт:** {REFLECTION['key_takeaway'].strip()}\n\n"
    report += f"**Критика AI:** {REFLECTION['tool_critique'].strip()}\n\n"

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/report_p1.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ Отчет успешно сгенерирован: artifacts/report_p1.md")

if __name__ == "__main__":
    export_report()
