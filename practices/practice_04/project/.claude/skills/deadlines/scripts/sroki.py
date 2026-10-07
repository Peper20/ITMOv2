#!/usr/bin/env python3
"""CLI к API трекера «Сроки»: дедлайны и категории. Только stdlib.

Адрес сервера — переменная SROKI_URL (по умолчанию http://127.0.0.1:8000).
Успех: JSON в stdout, код 0. Ошибка API или сети: {"error": ...} в stderr, код 1.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any

BASE_URL = os.environ.get("SROKI_URL", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_TIME = "23:59"
PRIORITY_NAMES = {"low": 1, "normal": 2, "high": 3, "1": 1, "2": 2, "3": 3}


class CliError(Exception):
    """Ошибка, которую нужно показать пользователю как {"error": ...}."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


def request(method: str, path: str, body: dict[str, Any] | None = None,
            query: dict[str, str] | None = None) -> Any:
    url = BASE_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as err:
        try:
            payload = json.loads(err.read() or b"{}")
        except json.JSONDecodeError:
            payload = {}
        raise CliError(f"HTTP {err.code}: {payload.get('error', err.reason)}",
                       payload.get("field")) from err
    except urllib.error.URLError as err:
        raise CliError(f"сервер {BASE_URL} недоступен: {err.reason}. "
                       "Запустите: python3 backend/server.py") from err
    return json.loads(raw) if raw else None


def parse_due(value: str) -> str:
    """'today' | 'tomorrow' | '+N' | YYYY-MM-DD | YYYY-MM-DDTHH:MM -> YYYY-MM-DDTHH:MM."""
    v = value.strip().replace(" ", "T")
    relative = {"today": 0, "сегодня": 0, "tomorrow": 1, "завтра": 1}
    if v.lower() in relative:
        day = date.today() + timedelta(days=relative[v.lower()])
        return f"{day.isoformat()}T{DEFAULT_TIME}"
    if v.startswith("+") and v[1:].isdigit():
        return f"{(date.today() + timedelta(days=int(v[1:]))).isoformat()}T{DEFAULT_TIME}"
    if len(v) == 10:
        return f"{v}T{DEFAULT_TIME}"
    return v[:16]


def resolve_category(value: str) -> int | None:
    """ID, 'none' или имя категории (без учёта регистра) -> category_id."""
    if value.lower() in ("none", "null", "-"):
        return None
    if value.isdigit():
        return int(value)
    categories: list[dict[str, Any]] = request("GET", "/api/categories")
    matches = [c for c in categories if c["name"].casefold() == value.casefold()]
    if not matches:
        matches = [c for c in categories if value.casefold() in c["name"].casefold()]
    if len(matches) != 1:
        names = ", ".join(c["name"] for c in (matches or categories)) or "категорий нет"
        reason = "неоднозначно" if matches else "не найдена"
        raise CliError(f"категория «{value}» {reason}; варианты: {names}", "category_id")
    return int(matches[0]["id"])


def parse_priority(value: str) -> int:
    if value.lower() not in PRIORITY_NAMES:
        raise CliError("приоритет: 1|2|3 или low|normal|high", "priority")
    return PRIORITY_NAMES[value.lower()]


def deadline_fields(args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if getattr(args, "title", None) is not None:
        body["title"] = args.title
    if args.due is not None:
        body["due_at"] = parse_due(args.due)
    if args.category is not None:
        body["category_id"] = resolve_category(args.category)
    if args.priority is not None:
        body["priority"] = parse_priority(args.priority)
    if args.description is not None:
        body["description"] = args.description
    if getattr(args, "status", None) is not None:
        body["status"] = args.status
    return body


def run(args: argparse.Namespace) -> Any:
    match args.command:
        case "health":
            return request("GET", "/api/health")
        case "stats":
            return request("GET", "/api/stats")
        case "categories":
            return request("GET", "/api/categories")
        case "list":
            query = {k: v for k, v in {
                "status": args.status, "q": args.q, "sort": args.sort,
                "from": args.date_from, "to": args.date_to,
            }.items() if v}
            if args.category is not None:
                cid = resolve_category(args.category)
                query["category_id"] = "none" if cid is None else str(cid)
            return request("GET", "/api/deadlines", query=query)
        case "get":
            return request("GET", f"/api/deadlines/{args.id}")
        case "add":
            body = deadline_fields(args)
            body["title"] = args.title
            return request("POST", "/api/deadlines", body)
        case "update":
            body = deadline_fields(args)
            if not body:
                raise CliError("нечего менять: укажите хотя бы одно поле")
            return request("PATCH", f"/api/deadlines/{args.id}", body)
        case "done" | "reopen":
            status = "done" if args.command == "done" else "todo"
            return request("PATCH", f"/api/deadlines/{args.id}", {"status": status})
        case "delete":
            before = request("GET", f"/api/deadlines/{args.id}")
            request("DELETE", f"/api/deadlines/{args.id}")
            return {"deleted": before}
        case _:
            raise CliError(f"неизвестная команда: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sroki", description="CLI к API трекера дедлайнов «Сроки»")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("health", help="проверить сервер")
    sub.add_parser("stats", help="сводка: overdue/today/week/open/done")
    sub.add_parser("categories", help="список категорий")

    ls = sub.add_parser("list", help="список дедлайнов с фильтрами")
    ls.add_argument("--status", choices=["todo", "in_progress", "done", "open"])
    ls.add_argument("--category", help="ID, имя или none")
    ls.add_argument("--q", help="подстрока в названии/описании")
    ls.add_argument("--from", dest="date_from", help="YYYY-MM-DD[THH:MM]")
    ls.add_argument("--to", dest="date_to", help="YYYY-MM-DD[THH:MM]")
    ls.add_argument("--sort", choices=["due", "priority", "created"])

    for name in ("get", "done", "reopen", "delete"):
        sub.add_parser(name).add_argument("id", type=int)

    def fields(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--due", help="today|tomorrow|+N|YYYY-MM-DD|YYYY-MM-DDTHH:MM")
        sp.add_argument("--category", help="ID, имя или none")
        sp.add_argument("--priority", help="1|2|3 или low|normal|high")
        sp.add_argument("--description")

    add = sub.add_parser("add", help="создать дедлайн")
    add.add_argument("title")
    fields(add)

    upd = sub.add_parser("update", help="изменить поля дедлайна")
    upd.add_argument("id", type=int)
    upd.add_argument("--title")
    upd.add_argument("--status", choices=["todo", "in_progress", "done"])
    fields(upd)
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "add" and args.due is None:
        args.due = "tomorrow"
    try:
        result = run(args)
    except CliError as err:
        out: dict[str, str] = {"error": str(err)}
        if err.field:
            out["field"] = err.field
        print(json.dumps(out, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
