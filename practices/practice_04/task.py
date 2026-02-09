import json
import os
from typing import List

"""
ПРАКТИКА 4: SPEC-DRIVEN РАЗРАБОТКА С AGENTS.MD
Курс: AI-инструменты в жизни инженера (ИТМО)

ИНСТРУКЦИЯ:
В этой практике мы используем Agents.md как единственный источник правды.
Все промпты начинаются с @Agents.md для гарантированной консистентности кода.
"""

STUDENT_INFO = {
    "full_name": "TODO: Фамилия Имя",
    "group_number": "TODO: Группа",
}

# =================================================================================================
# 1. ЖУРНАЛ SPEC-DRIVEN РАЗРАБОТКИ
# =================================================================================================

class SpecDrivenLog:
    def __init__(self, task: str, prompt_with_agents_md: str, result: str, agents_md_updated: bool, analysis: str):
        self.task = task                        # Какая задача? (напр. "Создание database.py")
        self.prompt_with_agents_md = prompt_with_agents_md  # Полный промпт с @Agents.md
        self.result = result                    # Что сгенерировал AI?
        self.agents_md_updated = agents_md_updated  # Обновили ли Agents.md после изменений?
        self.analysis = analysis                # Анализ: помог ли @Agents.md?

SPEC_DRIVEN_LOGS: List[SpecDrivenLog] = [
    # TODO: Заполните минимум 5 записей (по количеству основных задач)
    # Пример:
    # SpecDrivenLog(
    #     task="Создание database.py для SQLite",
    #     prompt_with_agents_md="@Agents.md Создай файл database.py с async функциями:\n- init_db()\n- create_subscription()\n- get_all_subscriptions()\n- delete_subscription_by_city()",
    #     result="AI создал database.py с правильным async/await, используя aiosqlite context manager",
    #     agents_md_updated=True,
    #     analysis="@Agents.md дал AI полный контекст: он знал про aiosqlite, async/await правила, naming conventions."
    # )
]

# =================================================================================================
# 2. СРАВНЕНИЕ: БЕЗ AGENTS.MD VS С AGENTS.MD
# =================================================================================================

COMPARISON_LOGS = {
    "without_agents_md": {
        "prompt": "TODO: Пример промпта БЕЗ @Agents.md (напр. просто 'создай database.py')",
        "result": "TODO: Что сгенерировал AI? (обычно несовместимый код)",
        "issues": "TODO: Проблемы (напр. использовал sync вместо async, неправильный naming)"
    },
    "with_agents_md": {
        "prompt": "TODO: Тот же промпт, но С @Agents.md",
        "result": "TODO: Что сгенерировал AI?",
        "improvements": "TODO: Улучшения (консистентность, правильные правила)"
    }
}

# =================================================================================================
# 3. ЧЕК-ЛИСТ РЕАЛИЗАЦИИ
# =================================================================================================

IMPLEMENTATION_CHECKLIST = {
    "agents_md_created": False,         # Agents.md создан из домашнего задания Практики 3
    "database_py_created": False,       # database.py с aiosqlite (async)
    "weather_service_created": False,   # weather_service.py с httpx (async)
    "weather_data_model": False,        # Pydantic модель WeatherData
    "get_weather_endpoint": False,      # GET /weather/{city} эндпоинт
    "agents_md_updated": False,         # Agents.md обновлен после изменений
    "env_configured": False,            # .env файл с OPENWEATHER_API_KEY
    "sqlite_migration_done": False,     # Миграция с in-memory на SQLite завершена
    "api_integration_tested": False,    # OpenWeatherMap API интеграция протестирована
}

# =================================================================================================
# 4. РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ API
# =================================================================================================

API_TEST_RESULTS = {
    "post_subscribe": {
        "request": "TODO: curl команда",
        "response": "TODO: JSON ответ",
        "db_check": "TODO: проверка в subscriptions.db"
    },
    "get_weather_valid": {
        "request": "TODO: curl http://localhost:8000/weather/Moscow",
        "response": "TODO: JSON с погодой"
    },
    "get_weather_invalid": {
        "request": "TODO: curl http://localhost:8000/weather/Narnia",
        "response": "TODO: 404 ошибка"
    },
    "get_subscriptions": {
        "request": "TODO: curl http://localhost:8000/subscriptions",
        "response": "TODO: список подписок из SQLite"
    }
}

# =================================================================================================
# 5. AGENTS.MD ЭВОЛЮЦИЯ
# =================================================================================================

AGENTS_MD_EVOLUTION = {
    "initial_version": """
    TODO: Скопируйте начальную версию Agents.md из домашнего задания Практики 3
    (Должна содержать: Project Overview, Tech Stack, Architecture, Development Rules, Current Tasks)
    """,

    "changes_made": [
        # TODO: Список изменений в Agents.md после каждой задачи
        # Пример:
        # {
        #     "task": "Добавление database.py",
        #     "section_updated": "Architecture",
        #     "change": "Добавлен компонент 'Database Layer (database.py): SQLite async operations, CRUD для subscriptions'"
        # }
    ],

    "final_version": """
    TODO: Скопируйте финальную версию Agents.md после всех обновлений
    """
}

# =================================================================================================
# 6. РЕФЛЕКСИЯ
# =================================================================================================

REFLECTION = {
    "spec_driven_benefits": """
    TODO: Какие преимущества дал spec-driven подход?
    Сравните с Практикой 3, где вы использовали @file, @codebase для каждого промпта.
    """,

    "agents_md_as_single_source": """
    TODO: Помог ли Agents.md как единый источник правды?
    Приведите пример, когда AI сгенерировал правильный код благодаря @Agents.md.
    """,

    "bidirectional_workflow": """
    TODO: Насколько важно обновлять Agents.md после изменений кода?
    Что произойдет, если Agents.md устареет?
    """,

    "async_challenges": """
    TODO: В чем была сложность работы с async/await (aiosqlite, httpx)?
    Как @Agents.md помог с этим?
    """,

    "comparison_with_practice3": """
    TODO: Сравните Практику 3 (контекст + правила) и Практику 4 (spec-driven).
    Какой подход эффективнее для сложных проектов?
    """
}

# =================================================================================================
# ЭКСПОРТ
# =================================================================================================

def export_report():
    report = f"# Отчет по Практике 4: {STUDENT_INFO['full_name']}\n\n"

    report += "## 1. Журнал Spec-Driven разработки\n\n"
    for log in SPEC_DRIVEN_LOGS:
        report += f"### Задача: {log.task}\n"
        report += f"**Промпт с @Agents.md:**\n```\n{log.prompt_with_agents_md}\n```\n"
        report += f"**Результат:** {log.result}\n"
        report += f"**Agents.md обновлен:** {'✅ Да' if log.agents_md_updated else '❌ Нет'}\n"
        report += f"**Анализ:** {log.analysis}\n"
        report += "---\n"

    report += "\n## 2. Сравнение: БЕЗ vs С Agents.md\n\n"
    report += "### БЕЗ @Agents.md:\n"
    report += f"**Промпт:** {COMPARISON_LOGS['without_agents_md']['prompt']}\n"
    report += f"**Результат:** {COMPARISON_LOGS['without_agents_md']['result']}\n"
    report += f"**Проблемы:** {COMPARISON_LOGS['without_agents_md']['issues']}\n\n"

    report += "### С @Agents.md:\n"
    report += f"**Промпт:** {COMPARISON_LOGS['with_agents_md']['prompt']}\n"
    report += f"**Результат:** {COMPARISON_LOGS['with_agents_md']['result']}\n"
    report += f"**Улучшения:** {COMPARISON_LOGS['with_agents_md']['improvements']}\n\n"

    report += "\n## 3. Статус реализации\n\n"
    for item, status in IMPLEMENTATION_CHECKLIST.items():
        icon = "✅" if status else "❌"
        report += f"- {icon} {item}\n"

    report += "\n## 4. Результаты тестирования API\n\n"
    report += "```json\n" + json.dumps(API_TEST_RESULTS, indent=2, ensure_ascii=False) + "\n```\n\n"

    report += "\n## 5. Эволюция Agents.md\n\n"
    report += f"**Начальная версия:**\n```markdown\n{AGENTS_MD_EVOLUTION['initial_version']}\n```\n\n"
    report += "**Изменения:**\n"
    for change in AGENTS_MD_EVOLUTION['changes_made']:
        if isinstance(change, dict):
            report += f"- **{change.get('task', 'N/A')}** → Секция '{change.get('section_updated', 'N/A')}': {change.get('change', 'N/A')}\n"
    report += f"\n**Финальная версия:**\n```markdown\n{AGENTS_MD_EVOLUTION['final_version']}\n```\n\n"

    report += "\n## 6. Рефлексия\n\n"
    report += f"**Преимущества spec-driven:** {REFLECTION['spec_driven_benefits']}\n\n"
    report += f"**Agents.md как единый источник правды:** {REFLECTION['agents_md_as_single_source']}\n\n"
    report += f"**Bidirectional workflow:** {REFLECTION['bidirectional_workflow']}\n\n"
    report += f"**Async challenges:** {REFLECTION['async_challenges']}\n\n"
    report += f"**Сравнение с Практикой 3:** {REFLECTION['comparison_with_practice3']}\n"

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/report_p4.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ Отчет успешно сгенерирован: artifacts/report_p4.md")

if __name__ == "__main__":
    export_report()
