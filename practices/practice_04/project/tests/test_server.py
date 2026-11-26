"""HTTP-тесты: сервер на порту 0 с временной БД и временным FRONTEND_DIR."""

from __future__ import annotations

import http.client
import json
import os
import socket
import tempfile
import threading
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from urllib.parse import urlencode

from backend import db, server


class ServerTestCase(unittest.TestCase):
    app: server.App
    tmp: tempfile.TemporaryDirectory[str]
    now: datetime | None = None  # фиксированное «сейчас» для сервера; None — реальное время
    built: bool = True  # False — FRONTEND_DIR пуст (фронтенд не собран)

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        front = root / "front"
        (front / "sub").mkdir(parents=True)
        if cls.built:
            (front / "index.html").write_text("<h1>Сроки</h1>", encoding="utf-8")
            (front / "app.js").write_text("console.log(1)", encoding="utf-8")
            (front / "style.css").write_text("body{}", encoding="utf-8")
            (front / "favicon.ico").write_bytes(b"\x00\x00\x01\x00")
            assets = front / "assets"
            assets.mkdir()
            for name in ("index-B4x9kQ1a.js", "index-Cz3f.css", "inter-latin.woff2", "inter-latin.woff",
                         "hero-9d1e.webp", "index-B4x9kQ1a.js.map", "manifest.json"):
                (assets / name).write_bytes(b"x")
        (root / "secret.txt").write_text("secret", encoding="utf-8")
        config = server.Config("127.0.0.1", 0, root / "test.db", front)
        fixed = cls.now
        cls.app = server.App(config, clock=(lambda: fixed) if fixed else datetime.now)
        threading.Thread(target=cls.app.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app.shutdown()
        cls.app.server_close()
        cls.tmp.cleanup()

    def request(
        self, method: str, path: str, body: object = None, raw: bytes | None = None
    ) -> tuple[int, dict[str, str], bytes]:
        conn = http.client.HTTPConnection("127.0.0.1", self.app.server_address[1], timeout=5)
        headers: dict[str, str] = {}
        data = raw
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        if data is not None:
            headers["Content-Type"] = "application/json"
        try:
            conn.request(method, path, body=data, headers=headers)
            resp = conn.getresponse()
            return resp.status, {k.lower(): v for k, v in resp.getheaders()}, resp.read()
        finally:
            conn.close()

    def api(self, method: str, path: str, body: object = None) -> tuple[int, object]:
        status, headers, data = self.request(method, path, body)
        if status == 204:
            self.assertEqual(data, b"")
            return status, None
        self.assertEqual(headers["content-type"], "application/json; charset=utf-8")
        return status, json.loads(data)

    def api_obj(self, method: str, path: str, body: object = None) -> tuple[int, dict[str, object]]:
        status, payload = self.api(method, path, body)
        assert isinstance(payload, dict)
        return status, {str(k): v for k, v in payload.items()}  # pyright: ignore[reportUnknownVariableType]


class ApiTests(ServerTestCase):
    def test_health(self) -> None:
        self.assertEqual(self.api("GET", "/api/health"), (200, {"status": "ok", "version": "1"}))

    def test_category_crud(self) -> None:
        status, cat = self.api_obj("POST", "/api/categories", {"name": "Курс", "kind": "study"})
        self.assertEqual(status, 201)
        self.assertEqual(cat["open_count"], 0)
        cid = cat["id"]
        status, again = self.api_obj("POST", "/api/categories", {"name": "курс", "kind": "work"})
        self.assertEqual(status, 409)
        self.assertEqual(again["field"], "name")
        self.assertIsInstance(again["error"], str)
        status, upd = self.api_obj("PATCH", f"/api/categories/{cid}", {"color": "#123456"})
        self.assertEqual((status, upd["color"]), (200, "#123456"))
        status, items = self.api("GET", "/api/categories")
        self.assertEqual(status, 200)
        assert isinstance(items, list)
        self.assertIn(cid, [c["id"] for c in items])  # pyright: ignore[reportUnknownVariableType]
        self.assertEqual(self.api("DELETE", f"/api/categories/{cid}"), (204, None))
        self.assertEqual(self.api_obj("DELETE", f"/api/categories/{cid}")[0], 404)

    def test_deadline_crud(self) -> None:
        status, dl = self.api_obj(
            "POST", "/api/deadlines", {"title": "ДЗ", "due_at": "2099-01-01T10:00", "priority": 3}
        )
        self.assertEqual(status, 201)
        self.assertEqual((dl["priority"], dl["status"], dl["is_overdue"]), (3, "todo", False))
        path = f"/api/deadlines/{dl['id']}"
        self.assertEqual(self.api_obj("GET", path)[1]["title"], "ДЗ")
        status, upd = self.api_obj("PATCH", path, {"status": "done"})
        self.assertEqual(status, 200)
        self.assertIsNotNone(upd["completed_at"])
        status, items = self.api("GET", "/api/deadlines")
        assert isinstance(items, list)
        self.assertEqual(status, 200)
        self.assertEqual(self.api("DELETE", path), (204, None))
        self.assertEqual(self.api_obj("GET", path)[0], 404)

    def test_validation_error_has_field(self) -> None:
        status, err = self.api_obj("POST", "/api/deadlines", {"title": "x", "due_at": "завтра"})
        self.assertEqual(status, 400)
        self.assertEqual(err["field"], "due_at")
        status, err = self.api_obj("POST", "/api/deadlines", {"title": "x", "due_at": "2099-01-01T10:00", "category_id": 999})
        self.assertEqual((status, err["field"]), (400, "category_id"))

    def test_bad_json(self) -> None:
        for raw in (b"{oops", b"[1, 2]", b"\xff\xfe"):
            with self.subTest(raw=raw):
                status, _, data = self.request("POST", "/api/categories", raw=raw)
                self.assertEqual(status, 400)
                self.assertIn("error", json.loads(data))
        status, _, _ = self.request("POST", "/api/categories")
        self.assertEqual(status, 400)

    def test_not_found_and_method_not_allowed(self) -> None:
        self.assertEqual(self.api_obj("GET", "/api/nope")[0], 404)
        self.assertEqual(self.api_obj("GET", "/api/deadlines/abc")[0], 404)
        self.assertEqual(self.api_obj("PATCH", "/api/categories/999", {"name": "x"})[0], 404)
        status, headers, _ = self.request("DELETE", "/api/deadlines")
        self.assertEqual(status, 405)
        self.assertEqual(headers["allow"], "GET, POST")
        self.assertEqual(self.api_obj("PUT", "/api/health")[0], 405)


    def test_body_too_large(self) -> None:
        conn = http.client.HTTPConnection("127.0.0.1", self.app.server_address[1], timeout=5)
        try:
            # Заявляем большой Content-Length: сервер должен отказать, не читая тело.
            conn.putrequest("POST", "/api/deadlines")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", str(server.MAX_BODY + 1))
            conn.endheaders()
            resp = conn.getresponse()
            self.assertEqual(resp.status, 413)
            self.assertIn("error", json.loads(resp.read()))
        finally:
            conn.close()

    def test_error_bodies_for_404_405(self) -> None:
        for method, path in (("GET", "/api/nope"), ("POST", "/api/stats"), ("GET", "/api/deadlines/999")):
            with self.subTest(path=path):
                status, err = self.api_obj(method, path, {} if method == "POST" else None)
                self.assertIn(status, (404, 405))
                self.assertIsInstance(err["error"], str)


class QueryTests(ServerTestCase):
    """Фильтры, сортировки и stats на фиксированном «сейчас» = 2026-10-06 12:00."""

    now = datetime(2026, 10, 6, 12, 0)
    ids: dict[str, int]
    cat: dict[str, object]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        helper = cls()
        _, mat = helper.api_obj("POST", "/api/categories", {"name": "Матан", "kind": "study"})
        _, work = helper.api_obj("POST", "/api/categories", {"name": "Работа", "kind": "work"})
        cls.cat = {"mat": mat["id"], "work": work["id"]}
        rows: list[tuple[str, dict[str, object]]] = [
            ("a", {"title": "Сдать ДЗ по матану", "due_at": "2026-10-05T10:00", "category_id": mat["id"], "priority": 3}),
            ("b", {"title": "Отчёт", "description": "Квартальный ОТЧЁТ для Ивана", "due_at": "2026-10-06T09:00",
                   "status": "in_progress", "priority": 1}),
            ("c", {"title": "Лаба 2", "due_at": "2026-10-06T18:00", "category_id": mat["id"]}),
            ("d", {"title": "Курсовая", "due_at": "2026-10-13T12:00", "category_id": work["id"], "priority": 3}),
            ("e", {"title": "Эссе", "due_at": "2026-10-13T12:01"}),
            ("f", {"title": "Старое дз", "due_at": "2026-10-01T10:00", "category_id": mat["id"], "status": "done"}),
        ]
        cls.ids = {}
        for key, body in rows:
            status, dl = helper.api_obj("POST", "/api/deadlines", body)
            assert status == 201, dl
            cls.ids[key] = int(str(dl["id"]))


    def keys(self, **params: object) -> list[str]:
        path = "/api/deadlines" + ("?" + urlencode(params) if params else "")
        status, items = self.api("GET", path)
        self.assertEqual(status, 200, items)
        assert isinstance(items, list)
        by_id = {v: k for k, v in self.ids.items()}
        return [by_id[item["id"]] for item in items]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]

    def test_default_is_bare_array_sorted_by_due(self) -> None:
        self.assertEqual(self.keys(), ["f", "a", "b", "c", "d", "e"])

    def test_status(self) -> None:
        self.assertEqual(self.keys(status="open"), ["a", "b", "c", "d", "e"])
        self.assertEqual(self.keys(status="done"), ["f"])
        self.assertEqual(self.keys(status="in_progress"), ["b"])
        self.assertEqual(self.keys(status="todo"), ["a", "c", "d", "e"])

    def test_category(self) -> None:
        self.assertEqual(self.keys(category_id=self.cat["mat"]), ["f", "a", "c"])
        self.assertEqual(self.keys(category_id="none"), ["b", "e"])
        self.assertEqual(self.keys(category_id=99999), [])

    def test_search_case_insensitive_cyrillic(self) -> None:
        self.assertEqual(self.keys(q="дз"), ["f", "a"])
        self.assertEqual(self.keys(q="ОТЧЁТ"), ["b"])
        self.assertEqual(self.keys(q="ивана"), ["b"])  # по description
        self.assertEqual(self.keys(q="%"), [])  # спецсимволы LIKE не работают как шаблон

    def test_date_range(self) -> None:
        self.assertEqual(self.keys(**{"from": "2026-10-06", "to": "2026-10-06"}), ["b", "c"])
        self.assertEqual(self.keys(**{"from": "2026-10-06T09:00", "to": "2026-10-13T12:00"}), ["b", "c", "d"])
        self.assertEqual(self.keys(to="2026-10-05"), ["f", "a"])
        self.assertEqual(self.keys(**{"from": "2026-10-13T12:01"}), ["e"])

    def test_sort(self) -> None:
        self.assertEqual(self.keys(sort="priority"), ["a", "d", "f", "c", "e", "b"])
        self.assertEqual(self.keys(sort="created"), ["f", "e", "d", "c", "b", "a"])
        self.assertEqual(self.keys(sort="due"), self.keys())

    def test_combinations(self) -> None:
        mat = self.cat["mat"]
        self.assertEqual(self.keys(status="open", category_id=mat), ["a", "c"])
        self.assertEqual(self.keys(status="open", category_id=mat, q="лаба"), ["c"])
        self.assertEqual(self.keys(status="open", sort="priority", **{"from": "2026-10-06"}), ["d", "c", "e", "b"])
        self.assertEqual(self.keys(category_id="none", status="todo", to="2026-10-13"), ["e"])

    def test_is_overdue_with_fixed_now(self) -> None:
        status, items = self.api("GET", "/api/deadlines")
        assert isinstance(items, list)
        overdue = {item["id"] for item in items if item["is_overdue"]}  # pyright: ignore[reportUnknownVariableType]
        self.assertEqual(overdue, {self.ids["a"], self.ids["b"]})

    def test_invalid_filters(self) -> None:
        cases = {
            "status": "status=all",
            "category_id": "category_id=abc",
            "from": "from=2026-13-01",
            "to": "to=tomorrow",
            "sort": "sort=title",
        }
        for field, qs in cases.items():
            with self.subTest(qs=qs):
                status, err = self.api_obj("GET", "/api/deadlines?" + qs)
                self.assertEqual((status, err["field"]), (400, field))

    def export(self, query: str = "") -> tuple[int, dict[str, str], str]:
        status, headers, body = self.request("GET", "/api/export.ics" + query)
        return status, headers, body.decode("utf-8")

    def test_export_headers_and_structure(self) -> None:
        status, headers, text = self.export()
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "text/calendar; charset=utf-8")
        self.assertEqual(headers["content-disposition"], 'attachment; filename="deadlines.ics"')
        self.assertTrue(text.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"))
        self.assertTrue(text.endswith("END:VCALENDAR\r\n"))
        self.assertNotIn("\n", text.replace("\r\n", ""))  # только CRLF
        lines = text.split("\r\n")[:-1]
        self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in lines))

    def test_export_default_is_open_only(self) -> None:
        _, _, text = self.export()
        uids = {f"UID:deadline-{self.ids[k]}@sroki" for k in "abcde"}
        self.assertEqual({line for line in text.split("\r\n") if line.startswith("UID:")}, uids)
        self.assertNotIn("STATUS:COMPLETED", text)

    def test_export_event_fields(self) -> None:
        _, _, text = self.export("?" + urlencode({"category_id": self.cat["mat"], "q": "лаба"}))
        event = text.split("BEGIN:VEVENT\r\n")[1].split("END:VEVENT")[0]
        self.assertIn(f"UID:deadline-{self.ids['c']}@sroki\r\n", event)
        self.assertIn("DTSTAMP:", event)
        self.assertRegex(event, r"DTSTAMP:\d{8}T\d{6}Z\r\n")
        self.assertIn("DTSTART:20261006T180000\r\n", event)
        self.assertIn("DTEND:20261006T183000\r\n", event)
        self.assertIn("SUMMARY:Лаба 2\r\n", event)
        self.assertIn("CATEGORIES:Матан\r\n", event)
        self.assertIn("PRIORITY:5\r\n", event)

    def test_export_filters(self) -> None:
        _, _, text = self.export("?status=done")
        self.assertEqual(text.count("BEGIN:VEVENT"), 1)
        self.assertIn("STATUS:COMPLETED", text)
        _, _, text = self.export("?category_id=none")
        self.assertEqual(text.count("BEGIN:VEVENT"), 2)
        status, headers, _ = self.request("GET", "/api/export.ics?sort=title")
        self.assertEqual((status, headers["content-type"]), (400, "application/json; charset=utf-8"))

    def test_stats(self) -> None:
        self.assertEqual(
            self.api("GET", "/api/stats"),
            (200, {"overdue": 2, "today": 2, "week": 2, "open": 5, "done": 1}),
        )


class IcsTests(unittest.TestCase):
    def test_escape(self) -> None:
        self.assertEqual(server.ics_escape("a\\b;c,d"), "a\\\\b\\;c\\,d")
        self.assertEqual(server.ics_escape("1\r\n2\n3\r4"), "1\\n2\\n3\\n4")
        self.assertEqual(server.ics_escape("Двоеточие: ок"), "Двоеточие: ок")

    def test_fold_short_line_untouched(self) -> None:
        self.assertEqual(server.ics_fold("SUMMARY:коротко"), "SUMMARY:коротко")
        line = "X" * 75
        self.assertEqual(server.ics_fold(line), line)

    def test_fold_ascii(self) -> None:
        folded = server.ics_fold("X" * 160)
        parts = folded.split("\r\n")
        self.assertEqual([len(p) for p in parts], [75, 75, 12])
        self.assertTrue(all(p.startswith(" ") for p in parts[1:]))
        self.assertEqual(folded.replace("\r\n ", ""), "X" * 160)

    def test_fold_does_not_split_multibyte(self) -> None:
        original = "SUMMARY:" + "Жё😀" * 30
        folded = server.ics_fold(original)
        for part in folded.split("\r\n"):
            raw = part.encode("utf-8")
            self.assertLessEqual(len(raw), 75)
            raw.decode("utf-8")  # каждая часть — целые символы
        self.assertEqual(folded.replace("\r\n ", ""), original)

    def test_build_ics_escapes_and_folds(self) -> None:
        dl = db.Deadline(
            id=1, title="Отчёт; итог, финал", description="Строка 1\nСтрока 2 " + "ы" * 60,
            due_at="2026-12-31T23:45", category_id=7, priority=3, status="todo",
            created_at="", updated_at="", completed_at=None, is_overdue=False,
        )
        text = server.build_ics([dl], {7: "Курс, 1"}, datetime(2026, 10, 6, 12, 0))
        self.assertIn("SUMMARY:Отчёт\\; итог\\, финал\r\n", text)
        self.assertIn("CATEGORIES:Курс\\, 1\r\n", text)
        self.assertIn("DTEND:20270101T001500\r\n", text)  # переход через год
        self.assertIn("PRIORITY:1\r\n", text)
        unfolded = text.replace("\r\n ", "")
        self.assertIn("DESCRIPTION:Строка 1\\nСтрока 2 " + "ы" * 60 + "\r\n", unfolded)
        self.assertIn("\r\n ", text)  # длинное описание действительно свёрнуто


class StaticTests(ServerTestCase):
    def test_index_and_content_types(self) -> None:
        cases = {
            "/": "text/html; charset=utf-8",
            "/index.html": "text/html; charset=utf-8",
            "/app.js": "text/javascript; charset=utf-8",
            "/style.css": "text/css; charset=utf-8",
        }
        for path, ctype in cases.items():
            with self.subTest(path=path):
                status, headers, _ = self.request("GET", path)
                self.assertEqual((status, headers["content-type"]), (200, ctype))
        _, _, body = self.request("GET", "/")
        self.assertEqual(body.decode("utf-8"), "<h1>Сроки</h1>")

    def test_head(self) -> None:
        status, headers, body = self.request("HEAD", "/app.js")
        self.assertEqual((status, body), (200, b""))
        self.assertEqual(headers["content-length"], str(len("console.log(1)")))

    def test_missing_and_traversal(self) -> None:
        for path in ("/missing.js", "/../secret.txt", "/%2e%2e/secret.txt", "/sub/..%2f..%2fsecret.txt"):
            with self.subTest(path=path):
                status, _, body = self.request("GET", path)
                self.assertEqual(status, 404)
                self.assertNotIn(b"secret", body)

    def test_post_static_not_allowed(self) -> None:
        status, _, _ = self.request("POST", "/index.html", raw=b"{}")
        self.assertEqual(status, 405)

    def test_vite_asset_content_types(self) -> None:
        cases = {
            "/assets/index-B4x9kQ1a.js": "text/javascript; charset=utf-8",
            "/assets/index-Cz3f.css": "text/css; charset=utf-8",
            "/assets/inter-latin.woff2": "font/woff2",
            "/assets/inter-latin.woff": "font/woff",
            "/assets/hero-9d1e.webp": "image/webp",
            "/assets/index-B4x9kQ1a.js.map": "application/json; charset=utf-8",
            "/assets/manifest.json": "application/json; charset=utf-8",
            "/favicon.ico": "image/x-icon",
        }
        for path, ctype in cases.items():
            with self.subTest(path=path):
                status, headers, _ = self.request("GET", path)
                self.assertEqual((status, headers["content-type"]), (200, ctype))

    def test_cache_control(self) -> None:
        immutable = "public, max-age=31536000, immutable"
        cases = {
            "/assets/index-B4x9kQ1a.js": immutable,
            "/assets/inter-latin.woff2": immutable,
            "/": "no-cache",
            "/index.html": "no-cache",
            "/app.js": "no-cache",
            "/favicon.ico": "no-cache",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                status, headers, _ = self.request("GET", path)
                self.assertEqual((status, headers["cache-control"]), (200, expected))
        _, headers, _ = self.request("HEAD", "/assets/index-Cz3f.css")
        self.assertEqual(headers["cache-control"], immutable)

    def test_missing_asset_is_404_json(self) -> None:
        status, headers, _ = self.request("GET", "/assets/missing-123.js")
        self.assertEqual((status, headers["content-type"]), (404, "application/json; charset=utf-8"))


class RequestLogTests(ServerTestCase):
    def raw_get(self, target: bytes) -> tuple[bytes, bytes]:
        """GET с произвольными байтами в URL (http.client не пропускает не-ASCII).

        Возвращает (статусная строка, тело)."""
        chunks: list[bytes] = []
        with socket.create_connection(("127.0.0.1", self.app.server_address[1]), timeout=5) as sock:
            sock.sendall(b"GET " + target + b" HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
            while chunk := sock.recv(65536):
                chunks.append(chunk)
        head, _, body = b"".join(chunks).partition(b"\r\n\r\n")
        return head.split(b"\r\n", 1)[0], body

    def logged(self, target: bytes) -> str:
        with self.assertLogs("sroki.server", level="INFO") as logs:
            self.raw_get(target)
        return "\n".join(logs.output)

    def test_cyrillic_query_is_readable(self) -> None:
        cases = (
            "/api/deadlines?q=тест".encode("utf-8"),  # сырые UTF-8 байты
            b"/api/deadlines?q=%D1%82%D0%B5%D1%81%D1%82",  # percent-encoding браузера
        )
        for target in cases:
            with self.subTest(target=target):
                output = self.logged(target)
                self.assertIn('"GET /api/deadlines?q=тест HTTP/1.1" 200', output)
                self.assertNotIn("Ñ", output)

    def test_raw_utf8_query_filters_like_percent_encoded(self) -> None:
        status, created = self.api_obj(
            "POST", "/api/deadlines", {"title": "Сырой тест запроса", "due_at": "2099-01-01T10:00"}
        )
        self.assertEqual(status, 201)
        self.api_obj("POST", "/api/deadlines", {"title": "Другое", "due_at": "2099-01-01T10:00"})
        for target in ("/api/deadlines?q=тест".encode("utf-8"), b"/api/deadlines?q=%D1%82%D0%B5%D1%81%D1%82"):
            with self.subTest(target=target):
                status_line, body = self.raw_get(target)
                self.assertIn(b" 200 ", status_line)
                found = json.loads(body)
                self.assertEqual([d["id"] for d in found], [created["id"]])

    def test_invalid_utf8_and_control_chars(self) -> None:
        output = self.logged(b"/api/deadlines?q=%FF%0Aforged")
        self.assertIn("q=\ufffd\\nforged", output)
        self.assertEqual(len(output.splitlines()), 1)  # перевод строки не разорвал запись


class FrontendNotBuiltTests(ServerTestCase):
    built = False

    def test_static_paths_return_503_page(self) -> None:
        for path in ("/", "/index.html", "/assets/index-B4x9kQ1a.js", "/some/page"):
            with self.subTest(path=path):
                status, headers, body = self.request("GET", path)
                self.assertEqual(status, 503)
                self.assertEqual(headers["content-type"], "text/html; charset=utf-8")
                self.assertEqual(headers["cache-control"], "no-store")
                text = body.decode("utf-8")
                self.assertIn("Фронтенд не собран", text)
                self.assertIn("cd frontend &amp;&amp; npm ci &amp;&amp; npm run build", text)

    def test_head_503_without_body(self) -> None:
        status, headers, body = self.request("HEAD", "/")
        self.assertEqual((status, body), (503, b""))
        self.assertGreater(int(headers["content-length"]), 0)

    def test_api_still_works(self) -> None:
        status, payload = self.api("GET", "/api/health")
        self.assertEqual((status, payload), (200, {"status": "ok", "version": "1"}))
        status, payload = self.api("GET", "/api/nope")
        self.assertEqual(status, 404)

    def test_build_appears_without_restart(self) -> None:
        front = self.app.config.frontend_dir
        (front / "index.html").write_text("<h1>ok</h1>", encoding="utf-8")
        try:
            status, _, body = self.request("GET", "/")
            self.assertEqual((status, body), (200, b"<h1>ok</h1>"))
        finally:
            (front / "index.html").unlink()


class FrontendConfigTests(unittest.TestCase):
    def test_default_frontend_dir_is_vite_dist(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            config = server.Config.from_env()
        self.assertEqual(config.frontend_dir, server.PROJECT_ROOT / "frontend" / "dist")

    def test_frontend_dir_override(self) -> None:
        with mock.patch.dict(os.environ, {"FRONTEND_DIR": "build"}, clear=True):
            self.assertEqual(server.Config.from_env().frontend_dir, server.PROJECT_ROOT / "build")
        with mock.patch.dict(os.environ, {"FRONTEND_DIR": "/srv/front"}, clear=True):
            self.assertEqual(server.Config.from_env().frontend_dir, Path("/srv/front"))

    def test_startup_warning_when_not_built(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = server.Config("127.0.0.1", 0, root / "test.db", root / "dist")
            with self.assertLogs("sroki.server", level="WARNING") as logs:
                app = server.App(config)
            app.server_close()
        self.assertIn("npm ci && npm run build", logs.output[0])

    def test_no_warning_when_built(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dist").mkdir()
            (root / "dist" / "index.html").write_text("ok", encoding="utf-8")
            config = server.Config("127.0.0.1", 0, root / "test.db", root / "dist")
            with self.assertNoLogs("sroki.server", level="WARNING"):
                app = server.App(config)
            app.server_close()


if __name__ == "__main__":
    unittest.main()
