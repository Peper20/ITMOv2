---
name: python-best-practices
description: Use when reading or writing Python files (.py) or pyright configuration (pyrightconfig.json) — typing idioms, error handling, logging, and type checking with pyright.
---

# Python Best Practices

Language-specific idioms for this project. Project-wide rules (stdlib only, tests on `unittest`) live in `.claude/rules/`. Type checking is done with **pyright** — the PostToolUse hook runs it after every edit of a `.py` file.

## Make Illegal States Unrepresentable

Use Python's type system so pyright rejects invalid states before the code runs.

**Frozen dataclasses for immutable domain models:**
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class User:
    id: str
    email: str
    name: str
    created_at: datetime

# Frozen dataclasses are immutable — pyright flags `user.name = "x"` as an error
```

**Discriminated unions + exhaustive `match`:**
```python
from dataclasses import dataclass
from typing import Literal, assert_never

@dataclass(frozen=True)
class Success:
    data: str
    status: Literal["success"] = "success"  # fields with defaults go after the rest

@dataclass(frozen=True)
class Failure:
    error: Exception
    status: Literal["error"] = "error"

RequestState = Success | Failure

def handle_state(state: RequestState) -> None:
    match state:
        case Success(data=data):
            render(data)
        case Failure(error=err):
            show_error(err)
        case _:
            assert_never(state)  # pyright errors here if a new variant is not handled
```

**NewType for domain primitives:**
```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def get_user(user_id: UserId) -> User:
    # pyright rejects get_user(OrderId(1)) and get_user(1)
    ...
```

**Protocol for structural typing:**
```python
from typing import Protocol

class Readable(Protocol):
    def read(self, n: int = -1) -> bytes: ...

def process_input(source: Readable) -> bytes:
    # Accepts any object with a matching read() — no inheritance required
    return source.read()
```

**Typing tips that keep pyright precise:**
- Use built-in generics and `|`: `list[str]`, `dict[str, int]`, `str | None` (not `List`, `Optional`).
- Narrow `X | None` explicitly (`if x is None: ...`) instead of silencing the error.
- Prefer `TypedDict` for JSON-shaped dicts (request bodies, API responses) over `dict[str, Any]`.
- Annotate return types of public functions; let pyright infer locals.

## Python-Specific Error Handling

Chain exceptions with `from err` to preserve the original traceback:
```python
try:
    data = json.loads(raw)
except json.JSONDecodeError as err:
    raise ValueError(f"invalid JSON payload: {err}") from err
```

Catch specific exceptions, never a bare `except:`.

## Structured Logging

Use a module-level logger with `%s` formatting (deferred string interpolation):
```python
import logging

logger = logging.getLogger(__name__)

def create_widget(name: str) -> Widget:
    logger.debug("creating widget: %s", name)
    widget = Widget(name=name)
    logger.debug("created widget id=%s", widget.id)
    return widget
```

## Type Checking with pyright

The hook (`.claude/hooks/lsp_diagnostics.py`) checks each edited file via `pyright-langserver` and returns errors in `additionalContext` — fix them before moving on. For a full-project check:

```bash
pyright                    # whole project (uses pyrightconfig.json if present)
pyright backend/db.py      # a single file
```

Optional config (`pyrightconfig.json` in the project root):
```json
{
  "include": ["backend", "tests"],
  "pythonVersion": "3.12",
  "typeCheckingMode": "standard"
}
```

Rules of thumb:
- Need stricter checks for one file — put `# pyright: strict` at its top.
- Suppress a false positive narrowly with the rule name: `# pyright: ignore[reportAttributeAccessIssue]`, never a bare `# type: ignore`. Add a short comment why.
- Unsure what pyright inferred — temporarily add `reveal_type(x)` and read the diagnostic, then remove it.
- Prefer `typing.cast` or a type guard over `Any` when you know more than the checker.
