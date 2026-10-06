#!/usr/bin/env python3
"""PostToolUse-хук: после правки .py-файла запускает LSP-сервер Python и возвращает диагностику агенту.

Сервер по умолчанию — pyright (`pyright-langserver --stdio`), меняется через LSP_CMD.
Хук — минимальный LSP-клиент: initialize → didOpen → ждёт publishDiagnostics → shutdown.
Если сервера нет или он завис — хук тихо выходит (не блокирует работу).
"""
import json
import os
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from queue import Empty, Queue
from typing import Any

LSP_CMD = os.environ.get("LSP_CMD", "pyright-langserver --stdio")
TIMEOUT = float(os.environ.get("LSP_TIMEOUT", "30"))
MAX_REPORTED = 20
SEVERITY = {1: "error", 2: "warning"}  # info/hint не показываем


def send(proc: subprocess.Popen[bytes], msg: dict[str, Any]) -> None:
    body = json.dumps(msg).encode()
    assert proc.stdin is not None
    proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    proc.stdin.flush()


def reader(proc: subprocess.Popen[bytes], out: "Queue[dict[str, Any] | None]") -> None:
    stream = proc.stdout
    assert stream is not None
    while True:
        length = 0
        while True:
            header = stream.readline()
            if not header:
                out.put(None)
                return
            header = header.strip()
            if not header:
                break
            if header.lower().startswith(b"content-length:"):
                length = int(header.split(b":", 1)[1])
        out.put(json.loads(stream.read(length)))


def get_diagnostics(file_path: Path, root: Path) -> list[dict[str, Any]]:
    argv = shlex.split(LSP_CMD)
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, cwd=root)
    inbox: "Queue[dict[str, Any] | None]" = Queue()
    threading.Thread(target=reader, args=(proc, inbox), daemon=True).start()
    uri = file_path.as_uri()
    diagnostics: list[dict[str, Any]] = []
    deadline = time.monotonic() + TIMEOUT
    try:
        send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "processId": os.getpid(), "rootUri": root.as_uri(),
            "capabilities": {"textDocument": {"publishDiagnostics": {}}},
        }})
        opened = False
        got = False
        while time.monotonic() < deadline:
            try:
                msg = inbox.get(timeout=1.0 if not got else 0.5)
            except Empty:
                if got:
                    break  # диагностика пришла, новых обновлений нет
                continue
            if msg is None:
                break
            method, mid = msg.get("method"), msg.get("id")
            if method is None and mid == 1 and not opened:
                send(proc, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
                send(proc, {"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {
                    "textDocument": {"uri": uri, "languageId": "python", "version": 1,
                                     "text": file_path.read_text(encoding="utf-8")}}})
                opened = True
            elif method == "textDocument/publishDiagnostics" and msg["params"]["uri"] == uri:
                diagnostics = msg["params"]["diagnostics"]
                got = True
            elif method is not None and mid is not None:  # запрос от сервера — отвечаем пустышкой
                result: Any = [None] * len(msg.get("params", {}).get("items", [])) \
                    if method == "workspace/configuration" else None
                send(proc, {"jsonrpc": "2.0", "id": mid, "result": result})
        try:
            send(proc, {"jsonrpc": "2.0", "id": 2, "method": "shutdown"})
            send(proc, {"jsonrpc": "2.0", "method": "exit"})
        except (BrokenPipeError, OSError):
            pass
    finally:
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
    return diagnostics


def main() -> int:
    try:
        event = json.load(sys.stdin)
        raw = (event.get("tool_input") or {}).get("file_path")
    except (json.JSONDecodeError, AttributeError):
        return 0
    if not raw or not raw.endswith(".py"):
        return 0
    file_path = Path(raw).resolve()
    if not file_path.is_file():
        return 0
    if shutil.which(shlex.split(LSP_CMD)[0]) is None:
        print(f"lsp_diagnostics: LSP-сервер не найден ({LSP_CMD}); проверка пропущена", file=sys.stderr)
        return 1  # неблокирующая ошибка: видна пользователю
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
    try:
        diags = get_diagnostics(file_path, root)
    except (OSError, ValueError, KeyError) as e:
        print(f"lsp_diagnostics: сбой LSP-клиента: {e}", file=sys.stderr)
        return 1
    issues = [d for d in diags if d.get("severity", 1) in SEVERITY]
    if not issues:
        return 0
    rel = os.path.relpath(file_path, root)
    lines = [f"LSP ({LSP_CMD.split()[0]}) нашёл проблемы в {rel}:"]
    for d in issues[:MAX_REPORTED]:
        start = d["range"]["start"]
        lines.append(f"- {rel}:{start['line'] + 1}:{start['character'] + 1} "
                     f"[{SEVERITY[d.get('severity', 1)]}] {d['message']}")
    if len(issues) > MAX_REPORTED:
        lines.append(f"... и ещё {len(issues) - MAX_REPORTED}")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                              "additionalContext": "\n".join(lines)}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
