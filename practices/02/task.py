import json
import os
from typing import List

"""
ПРАКТИКА 2: ПРОФЕССИОНАЛЬНЫЙ ПРОМПТИНГ (R.C.T.F.)
Курс: AI-инструменты в жизни инженера (ИТМО)

ИНСТРУКЦИЯ:
В этой практике мы учимся не просто "болтать" с AI, а программировать его поведение
с помощью фреймворка R.C.T.F. (Role, Context, Task, Format).
"""

# =================================================================================================
# 1. ИНФОРМАЦИЯ
# =================================================================================================
STUDENT_INFO = {
    "full_name": "TODO: Фамилия Имя",
    "group_number": "TODO: Группа",
    "date": "TODO: YYYY-MM-DD"
}

# =================================================================================================
# 2. ЖУРНАЛ R.C.T.F. (Самая важная часть!)
# =================================================================================================
class RCTF_Log:
    def __init__(self, task_name: str, role: str, context: str, task: str, format_instruction: str, result: str):
        self.task_name = task_name
        self.role = role             # R: Кто такой AI? (Senior QA, Architect...)
        self.context = context       # C: Контекст проекта (Веб-сервис, Python, FastAPI...)
        self.task = task             # T: Что конкретно сделать?
        self.format = format_instruction # F: В каком виде выдать ответ? (Markdown, Gherkin...)
        self.result = result         # Итог (кратко)

PROMPT_LOGS: List[RCTF_Log] = [
    # TODO: Заполните лог для каждого задания
    # Пример:
    # RCTF_Log(
    #     task_name="Gherkin Scenarios",
    #     role="Senior QA Engineer",
    #     context="Проект погодного сервиса, пользователь хочет подписаться через API.",
    #     task="Напиши сценарии для фичи подписки.",
    #     format="Gherkin syntax (Given/When/Then)",
    #     result="Сгенерировал 3 сценария для API endpoints, но забыл негативные кейсы."
    # )
]

# =================================================================================================
# 3. АРТЕФАКТЫ (Улучшенные версии из Практики 1)
# =================================================================================================

# Задание 1: Улучшенная Архитектура (Mermaid v2)
MERMAID_V2 = """
TODO: Вставьте улучшенный Mermaid код (с деталями протоколов, Redis кэш, PostgreSQL)
Должно включать: Client Apps → FastAPI Backend → Redis Cache → PostgreSQL DB → OpenWeatherMap API
"""

# Задание 2: Gherkin Scenarios (BDD)
GHERKIN_SCENARIOS = """
TODO: Вставьте сценарии в формате Gherkin
Feature: Weather Subscription API
  Scenario: Successful subscription via POST /subscribe
    Given клиент имеет валидный API endpoint
    When клиент отправляет POST /subscribe с {"city": "Moscow", "email": "user@test.com"}
    Then API возвращает 200 OK с данными о погоде
"""

# Задание 3: Улучшенные DoR и DoD v2.0
DOR_V2 = """
TODO: Вставьте улучшенный Definition of Ready v2.0 (структурированный по категориям)
"""

DOD_V2 = """
TODO: Вставьте улучшенный Definition of Done v2.0 (структурированный по категориям)
"""

# Задание 4: Тест-план v2 (Классифицированный)
TEST_PLAN_V2 = """
TODO: Тест-план, разбитый по уровням (Unit / Integration / E2E)
"""

# Задание 5: Улучшенный Functional Delivery v2.0
FUNCTIONAL_DELIVERY_V2 = """
TODO: Вставьте улучшенные Jira-тикеты (3-4 штуки) с детализацией:
- Детальные Acceptance Criteria
- Зависимости
- Приоритеты
- Оценки времени
- Детальные тест-кейсы
"""

# =================================================================================================
# 4. ДОМАШНЕЕ ЗАДАНИЕ (опционально)
# =================================================================================================

# Улучшение Event Storming v2.0 (опционально)
HOMEWORK_EVENT_STORMING_V2 = """
TODO: (Опционально) Улучшенный Event Storming с использованием R.C.T.F.
Добавьте больше событий, уточните команды и акторов.
"""

# Улучшение Roadmap v2.0 (опционально)
HOMEWORK_ROADMAP_V2 = """
TODO: (Опционально) Улучшенный Roadmap с использованием R.C.T.F.
Детализируйте версии, добавьте метрики успеха для каждой версии.
"""

# Chain of Thought (многоэтапный промптинг)
HOMEWORK_MULTIPROMPT_TASK = """
TODO: Опишите задачу, которую вы разбили на шаги
"""

HOMEWORK_MULTIPROMPT_STEPS = """
TODO: Список шагов (3-5 штук)
"""

HOMEWORK_MULTIPROMPT_SEQUENCE = """
TODO: Последовательность промптов с результатами каждого шага
"""

HOMEWORK_MULTIPROMPT_RESULT = """
TODO: Финальный результат после всех шагов
"""

# =================================================================================================
# 5. РЕФЛЕКСИЯ
# =================================================================================================
REFLECTION = {
    "before_after": """
    TODO: Сравните результаты "простого" промпта из Практики 1 и R.C.T.F. из Практики 2.
    В чем главная разница?
    """,
    
    "hardest_part": "TODO: Какая часть R.C.T.F. дается сложнее всего (Role, Context...)?",
}

# =================================================================================================
# ЭКСПОРТ
# =================================================================================================
def export_report():
    if "TODO" in STUDENT_INFO["full_name"]:
        print("❌ ОШИБКА: Заполните информацию о студенте.")
        return

    report = f"# Отчет по Практике 2: {STUDENT_INFO['full_name']}\n\n"
    report += "## 1. Анализ промптов R.C.T.F.\n\n"
    
    if not PROMPT_LOGS:
        report += "⚠️ Журнал пуст!\n"
    
    for log in PROMPT_LOGS:
        report += f"### {log.task_name}\n"
        report += f"**Role:** {log.role}\n"
        report += f"**Context:** {log.context}\n"
        report += f"**Task:** {log.task}\n"
        report += f"**Format:** {log.format}\n"
        report += f"**Результат:** {log.result}\n"
        report += "---\n"

    report += "## 2. Улучшенные артефакты\n\n"
    report += "### Mermaid v2\n```mermaid\n" + MERMAID_V2 + "\n```\n\n"
    report += "### Gherkin Scenarios\n```gherkin\n" + GHERKIN_SCENARIOS + "\n```\n\n"
    report += "### DoR v2.0\n" + DOR_V2 + "\n\n"
    report += "### DoD v2.0\n" + DOD_V2 + "\n\n"
    report += "### Test Plan v2\n" + TEST_PLAN_V2 + "\n\n"
    report += "### Functional Delivery v2.0\n" + FUNCTIONAL_DELIVERY_V2 + "\n\n"

    report += "## 3. Домашнее задание\n\n"
    if HOMEWORK_EVENT_STORMING_V2 and "TODO" not in HOMEWORK_EVENT_STORMING_V2:
        report += "### Event Storming v2.0\n" + HOMEWORK_EVENT_STORMING_V2 + "\n\n"
    if HOMEWORK_ROADMAP_V2 and "TODO" not in HOMEWORK_ROADMAP_V2:
        report += "### Roadmap v2.0\n" + HOMEWORK_ROADMAP_V2 + "\n\n"
    if HOMEWORK_MULTIPROMPT_TASK and "TODO" not in HOMEWORK_MULTIPROMPT_TASK:
        report += "### Chain of Thought\n"
        report += "**Задача:** " + HOMEWORK_MULTIPROMPT_TASK + "\n\n"
        report += "**Шаги:** " + HOMEWORK_MULTIPROMPT_STEPS + "\n\n"
        report += "**Последовательность:** " + HOMEWORK_MULTIPROMPT_SEQUENCE + "\n\n"
        report += "**Результат:** " + HOMEWORK_MULTIPROMPT_RESULT + "\n\n"
    
    report += "## 4. Рефлексия\n\n"
    report += f"**Before/After:** {REFLECTION['before_after']}\n\n"
    report += f"**Сложности:** {REFLECTION['hardest_part']}\n"

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/report_p2.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ Отчет успешно сгенерирован: artifacts/report_p2.md")

if __name__ == "__main__":
    export_report()
