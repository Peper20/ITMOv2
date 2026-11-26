#!/usr/bin/env python3
"""Минимальный MCP-сервер (stdio, JSON-RPC) для чтения SQLite. Только stdlib.

Tools:
  db_schema() — список таблиц и колонок
  db_query(sql, limit=100) — только чтение (SELECT/WITH/EXPLAIN), БД открыта в mode=ro
"""
import json
import os
import re
import sqlite3
import sys
from typing import Any

PROTOCOL_VERSION = "2024-11-05"
DB_PATH = os.environ.get("DB_PATH", "data/app.db")
MAX_LIMIT = 1000
READ_ONLY_RE = re.compile(r"^\s*(select|with|explain)\b", re.IGNORECASE)

TOOLS = [
    {
        "name": "db_schema",
        "description": "Показать таблицы SQLite-базы проекта и их колонки.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "db_query",
        "description": "Выполнить read-only SQL (SELECT/WITH/EXPLAIN) в базе проекта. "
        "Запросы на изменение данных отклоняются.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "Один SELECT-запрос"},
                "limit": {
                    "type": "integer",
                    "description": f"Максимум строк в ответе (1..{MAX_LIMIT}, по умолчанию 100)",
                },
            },
            "required": ["sql"],
        },
    },
]


class ToolError(Exception):
    """Ошибка входных данных или БД — возвращается модели как isError."""


def connect() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise ToolError(f"База данных не найдена: {DB_PATH} (она создаётся при первом запуске бэкенда)")
    conn = sqlite3.connect(f"file:{os.path.abspath(DB_PATH)}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def db_schema(_args: dict[str, Any]) -> Any:
    with connect() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        result = {}
        for t in tables:
            cols = conn.execute(f'PRAGMA table_info("{t["name"]}")').fetchall()
            result[t["name"]] = [
                {"name": c["name"], "type": c["type"], "notnull": bool(c["notnull"]), "pk": bool(c["pk"])}
                for c in cols
            ]
    return result


def db_query(args: dict[str, Any]) -> Any:
    sql = args.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        raise ToolError("Параметр 'sql' обязателен и должен быть непустой строкой")
    limit = args.get("limit", 100)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise ToolError(f"Параметр 'limit' должен быть целым числом от 1 до {MAX_LIMIT}")
    if not READ_ONLY_RE.match(sql):
        raise ToolError("Разрешены только запросы на чтение: SELECT, WITH или EXPLAIN")
    if ";" in sql.strip().rstrip(";"):
        raise ToolError("Разрешён только один SQL-запрос за вызов")
    try:
        with connect() as conn:
            cur = conn.execute(sql)
            rows = cur.fetchmany(limit + 1)
    except sqlite3.Error as e:
        raise ToolError(f"Ошибка SQLite: {e}") from e
    truncated = len(rows) > limit
    return {"rows": [dict(r) for r in rows[:limit]], "truncated": truncated}


HANDLERS = {"db_schema": db_schema, "db_query": db_query}


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    handler = HANDLERS.get(name)
    if handler is None:
        return {"isError": True, "content": [{"type": "text", "text": f"Неизвестный tool: {name}"}]}
    try:
        data = handler(args or {})
    except ToolError as e:
        return {"isError": True, "content": [{"type": "text", "text": str(e)}]}
    return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}]}


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    msg_id = msg.get("id")
    if msg_id is None:  # notification — ответа не требуется
        return None
    if method == "initialize":
        result: Any = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "sqlite-readonly", "version": "0.1.0"},
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = msg.get("params") or {}
        result = call_tool(params.get("name", ""), params.get("arguments") or {})
    elif method == "ping":
        result = {}
    else:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            reply: dict[str, Any] | None = {
                "jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"},
            }
        else:
            reply = handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
