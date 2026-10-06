"""Тесты слоя БД: миграции, CRUD и валидация (in-memory SQLite)."""

from __future__ import annotations

import sqlite3
import unittest
from datetime import datetime

from backend import db


class DbTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = db.connect(":memory:")
        db.migrate(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    def make_category(self, name: str = "Матанализ", kind: str = "study") -> db.Category:
        return db.create_category(self.conn, {"name": name, "kind": kind})

    def make_deadline(self, **fields: object) -> db.Deadline:
        data: dict[str, object] = {"title": "ДЗ", "due_at": "2099-01-01T10:00", **fields}
        return db.create_deadline(self.conn, data)

    def assert_invalid(self, field: str, func: object, *args: object) -> None:
        assert callable(func)
        with self.assertRaises(db.ValidationError) as ctx:
            func(*args)
        self.assertEqual(ctx.exception.field, field)


class MigrationTests(DbTestCase):
    def test_sets_user_version_and_is_idempotent(self) -> None:
        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertEqual(db.migrate(self.conn), 1)

    def test_keeps_foreign_tables(self) -> None:
        conn = db.connect(":memory:")
        conn.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
        conn.execute("INSERT INTO notes (text) VALUES ('x')")
        conn.commit()
        db.migrate(conn)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0], 1)
        conn.close()

    def test_foreign_keys_enabled(self) -> None:
        self.assertEqual(self.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)


class CategoryTests(DbTestCase):
    def test_create_defaults(self) -> None:
        cat = self.make_category()
        self.assertEqual(cat["name"], "Матанализ")
        self.assertEqual(cat["color"], "#888888")
        self.assertEqual(cat["open_count"], 0)
        self.assertRegex(cat["created_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$")

    def test_name_is_stripped_and_color_normalized(self) -> None:
        cat = db.create_category(self.conn, {"name": "  Работа ", "kind": "work", "color": "#AABBCC"})
        self.assertEqual(cat["name"], "Работа")
        self.assertEqual(cat["color"], "#aabbcc")

    def test_list_sorted_by_name(self) -> None:
        for name in ("в", "Б", "а", "b", "A"):
            self.make_category(name)
        names = [c["name"] for c in db.list_categories(self.conn)]
        self.assertEqual(names, ["A", "b", "а", "Б", "в"])

    def test_duplicate_name_conflict_case_insensitive(self) -> None:
        self.make_category("Proj")
        self.make_category("Курс")
        for name in ("proj", "курс", "КУРС"):
            with self.subTest(name=name), self.assertRaises(db.ConflictError) as ctx:
                self.make_category(name)
            self.assertEqual(ctx.exception.field, "name")

    def test_validation(self) -> None:
        cases: list[tuple[str, dict[str, object]]] = [
            ("name", {"kind": "study"}),
            ("kind", {"name": "x"}),
            ("name", {"name": "   ", "kind": "study"}),
            ("name", {"name": "x" * 61, "kind": "study"}),
            ("name", {"name": 5, "kind": "study"}),
            ("kind", {"name": "x", "kind": "hobby"}),
            ("color", {"name": "x", "kind": "study", "color": "red"}),
            ("color", {"name": "x", "kind": "study", "color": "#12345"}),
            ("extra", {"name": "x", "kind": "study", "extra": 1}),
        ]
        for field, data in cases:
            with self.subTest(data=data):
                self.assert_invalid(field, db.create_category, self.conn, data)

    def test_update_partial(self) -> None:
        cat = self.make_category()
        updated = db.update_category(self.conn, cat["id"], {"color": "#112233"})
        self.assertEqual(updated["color"], "#112233")
        self.assertEqual(updated["name"], cat["name"])

    def test_update_duplicate_conflict(self) -> None:
        self.make_category("A")
        b = self.make_category("B")
        with self.assertRaises(db.ConflictError):
            db.update_category(self.conn, b["id"], {"name": "a"})
        # переименование в то же имя с другим регистром — не конфликт с самим собой
        self.assertEqual(db.update_category(self.conn, b["id"], {"name": "b"})["name"], "b")

    def test_update_and_delete_missing(self) -> None:
        with self.assertRaises(db.NotFoundError):
            db.update_category(self.conn, 999, {"name": "x"})
        with self.assertRaises(db.NotFoundError):
            db.delete_category(self.conn, 999)

    def test_delete_keeps_deadlines(self) -> None:
        cat = self.make_category()
        dl = self.make_deadline(category_id=cat["id"])
        db.delete_category(self.conn, cat["id"])
        self.assertIsNone(db.get_deadline(self.conn, dl["id"])["category_id"])

    def test_open_count(self) -> None:
        cat = self.make_category()
        self.make_deadline(category_id=cat["id"])
        self.make_deadline(category_id=cat["id"], status="done")
        self.assertEqual(db.get_category(self.conn, cat["id"])["open_count"], 1)


class DeadlineTests(DbTestCase):
    def test_create_defaults(self) -> None:
        dl = self.make_deadline(title="  Сдать ДЗ  ")
        self.assertEqual(dl["title"], "Сдать ДЗ")
        self.assertEqual(dl["description"], "")
        self.assertEqual(dl["priority"], 2)
        self.assertEqual(dl["status"], "todo")
        self.assertIsNone(dl["category_id"])
        self.assertIsNone(dl["completed_at"])
        self.assertFalse(dl["is_overdue"])
        self.assertEqual(dl["created_at"], dl["updated_at"])

    def test_is_overdue(self) -> None:
        self.assertTrue(self.make_deadline(due_at="2000-01-01T00:00")["is_overdue"])
        self.assertFalse(self.make_deadline(due_at="2000-01-01T00:00", status="done")["is_overdue"])

    def test_create_done_sets_completed_at(self) -> None:
        self.assertIsNotNone(self.make_deadline(status="done")["completed_at"])

    def test_validation(self) -> None:
        base: dict[str, object] = {"title": "x", "due_at": "2099-01-01T10:00"}
        cases: list[tuple[str, dict[str, object]]] = [
            ("title", {"due_at": "2099-01-01T10:00"}),
            ("due_at", {"title": "x"}),
            ("title", {**base, "title": " "}),
            ("title", {**base, "title": "x" * 201}),
            ("description", {**base, "description": "x" * 5001}),
            ("description", {**base, "description": None}),
            ("due_at", {**base, "due_at": "2099-01-01"}),
            ("due_at", {**base, "due_at": "2099-02-30T10:00"}),
            ("due_at", {**base, "due_at": "2099-01-01T25:00"}),
            ("priority", {**base, "priority": 4}),
            ("priority", {**base, "priority": True}),
            ("priority", {**base, "priority": "1"}),
            ("status", {**base, "status": "open"}),
            ("category_id", {**base, "category_id": 42}),
            ("category_id", {**base, "category_id": "1"}),
            ("owner", {**base, "owner": "me"}),
        ]
        for field, data in cases:
            with self.subTest(data=data):
                self.assert_invalid(field, db.create_deadline, self.conn, data)

    def test_list_sorted_by_due(self) -> None:
        self.make_deadline(title="b", due_at="2099-02-01T10:00")
        self.make_deadline(title="a", due_at="2099-01-01T10:00")
        self.assertEqual([d["title"] for d in db.list_deadlines(self.conn)], ["a", "b"])

    def test_update_partial_and_category_reset(self) -> None:
        cat = self.make_category()
        dl = self.make_deadline(category_id=cat["id"], description="d")
        updated = db.update_deadline(self.conn, dl["id"], {"priority": 3, "category_id": None})
        self.assertEqual(updated["priority"], 3)
        self.assertIsNone(updated["category_id"])
        self.assertEqual(updated["description"], "d")

    def test_status_transitions_completed_at(self) -> None:
        dl = self.make_deadline()
        done = db.update_deadline(self.conn, dl["id"], {"status": "done"})
        self.assertIsNotNone(done["completed_at"])
        again = db.update_deadline(self.conn, dl["id"], {"status": "done", "priority": 1})
        self.assertEqual(again["completed_at"], done["completed_at"])
        reopened = db.update_deadline(self.conn, dl["id"], {"status": "in_progress"})
        self.assertIsNone(reopened["completed_at"])

    def test_update_validation_and_missing(self) -> None:
        dl = self.make_deadline()
        self.assert_invalid("title", db.update_deadline, self.conn, dl["id"], {"title": ""})
        with self.assertRaises(db.NotFoundError):
            db.update_deadline(self.conn, 999, {"title": "x"})
        with self.assertRaises(db.NotFoundError):
            db.get_deadline(self.conn, 999)

    def test_delete(self) -> None:
        dl = self.make_deadline()
        db.delete_deadline(self.conn, dl["id"])
        with self.assertRaises(db.NotFoundError):
            db.delete_deadline(self.conn, dl["id"])

    def test_schema_checks_still_enforced(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO deadlines (title, due_at, priority, created_at, updated_at)"
                " VALUES ('x', '2099-01-01T00:00', 9, 'a', 'a')"
            )


NOW = datetime(2026, 10, 6, 12, 0)


class FilterParseTests(unittest.TestCase):
    def test_defaults_and_empty_values(self) -> None:
        self.assertEqual(db.parse_deadline_filter({}), db.DeadlineFilter())
        empty = {"status": "", "category_id": "", "q": "  ", "from": "", "to": "", "sort": ""}
        self.assertEqual(db.parse_deadline_filter(empty), db.DeadlineFilter())
        self.assertEqual(db.parse_deadline_filter({"unknown": "x"}), db.DeadlineFilter())

    def test_parsed_values(self) -> None:
        f = db.parse_deadline_filter(
            {"status": "open", "category_id": "3", "q": " ДЗ ", "from": "2026-10-01",
             "to": "2026-10-07", "sort": "priority"}
        )
        self.assertEqual(
            f, db.DeadlineFilter("open", 3, False, "ДЗ", "2026-10-01T00:00", "2026-10-07T23:59", "priority")
        )
        f = db.parse_deadline_filter({"category_id": "none", "from": "2026-10-01T08:30", "to": "2026-10-01T09:00"})
        self.assertTrue(f.without_category)
        self.assertEqual((f.due_from, f.due_to), ("2026-10-01T08:30", "2026-10-01T09:00"))

    def test_invalid(self) -> None:
        cases = [
            ("status", {"status": "all"}),
            ("category_id", {"category_id": "-1"}),
            ("category_id", {"category_id": "abc"}),
            ("category_id", {"category_id": "١"}),  # не-ASCII цифра
            ("from", {"from": "01.10.2026"}),
            ("from", {"from": "2026-02-30"}),
            ("to", {"to": "2026-10-01T24:00"}),
            ("to", {"to": "2026-10-01T10:00:00"}),
            ("to", {"from": "2026-10-02", "to": "2026-10-01"}),
            ("sort", {"sort": "title"}),
            ("q", {"q": "x" * 201}),
        ]
        for field, query in cases:
            with self.subTest(query=query), self.assertRaises(db.ValidationError) as ctx:
                db.parse_deadline_filter(query)
            self.assertEqual(ctx.exception.field, field)


class StatsTests(DbTestCase):
    def test_empty(self) -> None:
        self.assertEqual(db.stats(self.conn, NOW), {"overdue": 0, "today": 0, "week": 0, "open": 0, "done": 0})

    def test_boundaries(self) -> None:
        for due, status in [
            ("2026-10-05T23:59", "todo"),         # overdue
            ("2026-10-06T00:00", "in_progress"),  # overdue + today
            ("2026-10-06T12:00", "todo"),         # today + week (now включительно, не overdue)
            ("2026-10-06T23:59", "todo"),         # today + week
            ("2026-10-13T12:00", "todo"),         # week (граница +7 суток включительно)
            ("2026-10-13T12:01", "todo"),         # только open
            ("2026-10-06T10:00", "done"),         # только done
        ]:
            self.make_deadline(due_at=due, status=status)
        self.assertEqual(db.stats(self.conn, NOW), {"overdue": 2, "today": 3, "week": 3, "open": 6, "done": 1})

    def test_is_overdue_uses_injected_now(self) -> None:
        dl = self.make_deadline(due_at="2026-10-06T11:59")
        self.assertTrue(db.get_deadline(self.conn, dl["id"], NOW)["is_overdue"])
        self.assertFalse(db.get_deadline(self.conn, dl["id"], datetime(2026, 10, 6, 11, 0))["is_overdue"])
        self.assertTrue(db.list_deadlines(self.conn, now=NOW)[0]["is_overdue"])


if __name__ == "__main__":
    unittest.main()
