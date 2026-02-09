"""
Тесты для Практики 01: Планирование разработки с использованием AI
"""
import pytest
from pathlib import Path
import os


class TestPractice01:
    """Тесты для практики 01"""

    def test_export_report_generates_file(self, tmp_path, monkeypatch):
        """
        Проверяем, что `export_report()` создаёт `artifacts/report_p1.md`
        и что в отчёте присутствуют ключевые секции новой версии практики.
        """
        monkeypatch.chdir(tmp_path)

        # Импортируем task.py из практики
        # Важно: импорт делаем внутри теста, чтобы monkeypatch.chdir успел сработать.
        from practices.practice_01 import task as p1_task  # type: ignore

        # Минимально заполняем обязательные поля, чтобы export_report не упал на TODO
        p1_task.STUDENT_INFO["full_name"] = "TEST STUDENT"
        p1_task.STUDENT_INFO["group_number"] = "TEST"
        p1_task.STUDENT_INFO["members"] = "Tester"
        p1_task.STUDENT_INFO["date"] = "2025-12-15"

        p1_task.EVENT_STORMING = "Actors/Commands/Events"
        p1_task.CJM = "CJM"
        p1_task.ROADMAP = "Roadmap"
        p1_task.EPICS = "Epics"
        p1_task.USER_STORIES = "User stories"
        p1_task.DEFINITION_OF_READY = "DoR"
        p1_task.ARCHITECTURE_COMPONENTS = "Components"
        p1_task.ADR = "ADR"
        p1_task.MERMAID_CODE = "graph TB\nA[Client] --> B[FastAPI]"
        p1_task.MERMAID_IMAGE_URL = "./board.png"
        p1_task.DEFINITION_OF_DONE = "DoD"
        p1_task.TEST_PLAN = "Test plan"
        p1_task.FUNCTIONAL_DELIVERY = "Tickets"
        p1_task.HOMEWORK_LLD = "LLD"
        p1_task.HOMEWORK_DOR_V2 = "DoR v2"
        p1_task.HOMEWORK_DOD_V2 = "DoD v2"
        p1_task.EDGE_CASES = "Edge cases"

        p1_task.PROMPT_LOGS = []
        p1_task.REFLECTION["key_takeaway"] = "ok"
        p1_task.REFLECTION["tool_critique"] = "ok"
        p1_task.REFLECTION["time_saved_estimate"] = "ok"

        p1_task.export_report()

        report_path = tmp_path / "artifacts" / "report_p1.md"
        assert report_path.exists()

        text = report_path.read_text(encoding="utf-8")
        assert "## 1. Бизнес-артефакты и планирование" in text
        assert "### Event storming" in text
        assert "### CJM" in text
        assert "### Roadmap" in text
        assert "### Epics" in text
        assert "## 2. Архитектура" in text
        assert "### ADR" in text
        assert "```mermaid" in text
        assert "### Functional Delivery" in text
        assert "## 4. Домашнее задание" in text


def test_example_hello_world():
    """Простой sanity-check для пайплайна тестов"""
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
