#!/usr/bin/env python3
"""PreToolUse-хук: перед правкой/созданием .py-файла требует, чтобы был загружен скил python-best-practices.

Скил считается загруженным, если:
- PostToolUse на Skill (этот же скрипт) оставил маркер сессии — нужен, т.к. транскрипт
  пишется на диск с задержкой и сразу после вызова Skill в нём ещё нет;
- или в транскрипте (transcript_path) есть вызов Skill / slash-команда /python-best-practices.
После сжатия контекста (compact_boundary) скил считается выгруженным. Если скил не загружен —
вызов отклоняется, и агент получает указание сначала загрузить скил.
При любой ошибке хук не мешает работе (exit 0).
"""
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILL = "python-best-practices"
COMMAND_TAG = f"<command-name>/{SKILL}</command-name>"
MARKER_DIR = Path(tempfile.gettempdir()) / "claude-python-skill"


def is_skill_use(block: Any) -> bool:
    return (isinstance(block, dict) and block.get("type") == "tool_use"
            and block.get("name") == "Skill"
            and (block.get("input") or {}).get("skill") == SKILL)


def scan_transcript(transcript: Path) -> tuple[bool, int]:
    """Возвращает (скил загружен после последнего сжатия, число сжатий контекста)."""
    loaded = False
    compactions = 0
    with transcript.open(encoding="utf-8") as f:
        for line in f:
            if '"compact_boundary"' in line:
                try:
                    if json.loads(line).get("subtype") == "compact_boundary":
                        loaded = False
                        compactions += 1
                except json.JSONDecodeError:
                    pass
                continue
            if SKILL not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = (entry.get("message") or {}).get("content")
            if isinstance(content, str):
                loaded = loaded or COMMAND_TAG in content
            elif isinstance(content, list):
                loaded = loaded or any(
                    is_skill_use(b) or (isinstance(b, dict) and COMMAND_TAG in str(b.get("text", "")))
                    for b in content)
    return loaded, compactions


def main() -> int:
    try:
        event = json.load(sys.stdin)
        tool_input = event.get("tool_input") or {}
        transcript = Path(event["transcript_path"])
        marker = MARKER_DIR / str(event["session_id"])
    except (json.JSONDecodeError, AttributeError, KeyError, TypeError):
        return 0
    try:
        if event.get("hook_event_name") == "PostToolUse":  # скил только что загружен
            if tool_input.get("skill") == SKILL:
                MARKER_DIR.mkdir(exist_ok=True)
                marker.write_text(str(scan_transcript(transcript)[1]))
            return 0
        if not str(tool_input.get("file_path") or "").endswith(".py"):
            return 0
        loaded, compactions = scan_transcript(transcript)
        if loaded or (marker.is_file() and marker.read_text().strip() == str(compactions)):
            return 0
    except (OSError, ValueError):
        return 0
    reason = (f"Перед правкой Python-файлов загрузи скил `{SKILL}` (инструмент Skill, "
              f'skill="{SKILL}"), затем повтори это действие.')
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": "deny",
                                              "permissionDecisionReason": reason}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
