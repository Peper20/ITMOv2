"""
Тесты для Практики 02: Профессиональный промптинг с R.C.T.F.
"""
import pytest
from pathlib import Path
import os


class TestPractice02:
    """Тесты для практики 02"""

    def test_export_report_generates_file(self, tmp_path, monkeypatch):
        """
        Проверяем, что `export_report()` создаёт `artifacts/report_p2.md`
        и что в отчёте присутствуют ключевые секции практики.
        """
        monkeypatch.chdir(tmp_path)

        # Импортируем task.py из практики
        # Важно: импорт делаем внутри теста, чтобы monkeypatch.chdir успел сработать.
        from practices.practice_02 import task as p2_task  # type: ignore

        # Минимально заполняем обязательные поля, чтобы export_report не упал на TODO
        p2_task.STUDENT_INFO["full_name"] = "TEST STUDENT"
        p2_task.STUDENT_INFO["group_number"] = "TEST"
        p2_task.STUDENT_INFO["date"] = "2025-12-15"

        # Заполняем артефакты
        p2_task.MERMAID_V2 = "graph TB\nA[Client] --> B[FastAPI]"
        p2_task.GHERKIN_SCENARIOS = "Feature: Test\n  Scenario: Test case"
        p2_task.DOR_V2 = "DoR v2.0 checklist"
        p2_task.DOD_V2 = "DoD v2.0 checklist"
        p2_task.TEST_PLAN_V2 = "| ID | Level | Test |"
        p2_task.FUNCTIONAL_DELIVERY_V2 = "Ticket 1: Description"

        # Заполняем домашнее задание (опционально)
        p2_task.HOMEWORK_EVENT_STORMING_V2 = "Event Storming v2"
        p2_task.HOMEWORK_ROADMAP_V2 = "Roadmap v2"
        p2_task.HOMEWORK_MULTIPROMPT_TASK = "Test task"
        p2_task.HOMEWORK_MULTIPROMPT_STEPS = "Step 1, Step 2"
        p2_task.HOMEWORK_MULTIPROMPT_SEQUENCE = "Prompt sequence"
        p2_task.HOMEWORK_MULTIPROMPT_RESULT = "Final result"

        # Заполняем R.C.T.F. логи
        p2_task.PROMPT_LOGS = [
            p2_task.RCTF_Log(
                task_name="Test Task",
                role="Test Role",
                context="Test Context",
                task="Test Task",
                format_instruction="Test Format",
                result="Test Result"
            )
        ]

        # Заполняем рефлексию
        p2_task.REFLECTION["before_after"] = "Test comparison"
        p2_task.REFLECTION["hardest_part"] = "Test difficulty"

        p2_task.export_report()

        report_path = tmp_path / "artifacts" / "report_p2.md"
        assert report_path.exists()

        text = report_path.read_text(encoding="utf-8")
        
        # Проверяем основные секции
        assert "## 1. Анализ промптов R.C.T.F." in text
        assert "## 2. Улучшенные артефакты" in text
        assert "## 3. Домашнее задание" in text
        assert "## 4. Рефлексия" in text
        
        # Проверяем артефакты
        assert "### Mermaid v2" in text
        assert "```mermaid" in text
        assert "### Gherkin Scenarios" in text
        assert "```gherkin" in text
        assert "### DoR v2.0" in text
        assert "### DoD v2.0" in text
        assert "### Test Plan v2" in text
        assert "### Functional Delivery v2.0" in text
        
        # Проверяем R.C.T.F. логи
        assert "### Test Task" in text
        assert "**Role:** Test Role" in text
        assert "**Context:** Test Context" in text
        assert "**Task:** Test Task" in text
        assert "**Format:** Test Format" in text
        assert "**Результат:** Test Result" in text
        
        # Проверяем домашнее задание
        assert "### Event Storming v2.0" in text
        assert "### Roadmap v2.0" in text
        assert "### Chain of Thought" in text
        assert "**Задача:** Test task" in text
        
        # Проверяем рефлексию
        assert "**Before/After:** Test comparison" in text
        assert "**Сложности:** Test difficulty" in text

    def test_export_report_without_homework(self, tmp_path, monkeypatch):
        """
        Проверяем, что отчёт генерируется даже без домашнего задания.
        """
        monkeypatch.chdir(tmp_path)

        from practices.practice_02 import task as p2_task  # type: ignore

        p2_task.STUDENT_INFO["full_name"] = "TEST STUDENT"
        p2_task.STUDENT_INFO["group_number"] = "TEST"
        p2_task.STUDENT_INFO["date"] = "2025-12-15"

        # Заполняем только обязательные артефакты
        p2_task.MERMAID_V2 = "graph TB"
        p2_task.GHERKIN_SCENARIOS = "Feature: Test"
        p2_task.DOR_V2 = "DoR"
        p2_task.DOD_V2 = "DoD"
        p2_task.TEST_PLAN_V2 = "Test plan"
        p2_task.FUNCTIONAL_DELIVERY_V2 = "Tickets"

        p2_task.PROMPT_LOGS = []
        p2_task.REFLECTION["before_after"] = "Test"
        p2_task.REFLECTION["hardest_part"] = "Test"

        p2_task.export_report()

        report_path = tmp_path / "artifacts" / "report_p2.md"
        assert report_path.exists()

        text = report_path.read_text(encoding="utf-8")
        assert "## 1. Анализ промптов R.C.T.F." in text
        assert "⚠️ Журнал пуст!" in text  # Должно быть предупреждение о пустом журнале


def test_example_hello_world():
    """Простой sanity-check для пайплайна тестов"""
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
