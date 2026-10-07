"""Работа с SQLite: соединение, миграции, репозитории категорий и дедлайнов.

Модуль ничего не знает про HTTP. Входные данные — JSON-подобные словари,
ошибки — исключения ValidationError / NotFoundError / ConflictError.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

# --- Исключения ---------------------------------------------------------------


class ValidationError(Exception):
    """Невалидное значение поля (HTTP 400)."""

    def __init__(self, field: str | None, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


class NotFoundError(Exception):
    """Объект не найден (HTTP 404)."""


class ConflictError(Exception):
    """Конфликт с существующими данными, например дубль имени (HTTP 409)."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


# --- Соединение и миграции ---------------------------------------------------


def connect(path: str | Path) -> sqlite3.Connection:
    """Открывает соединение с включёнными внешними ключами и row_factory=Row."""
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Регистронезависимый поиск с кириллицей: встроенные LIKE/lower() понимают только ASCII.
    conn.create_function("py_casefold", 1, _casefold, deterministic=True)
    return conn


def _casefold(value: str | None) -> str | None:
    return value.casefold() if value is not None else None



def _migration_1(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
          id         INTEGER PRIMARY KEY,
          name       TEXT NOT NULL UNIQUE COLLATE NOCASE,
          kind       TEXT NOT NULL CHECK (kind IN ('study','work','other')),
          color      TEXT NOT NULL DEFAULT '#888888',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deadlines (
          id           INTEGER PRIMARY KEY,
          title        TEXT NOT NULL,
          description  TEXT NOT NULL DEFAULT '',
          due_at       TEXT NOT NULL,
          category_id  INTEGER REFERENCES categories(id) ON DELETE SET NULL,
          priority     INTEGER NOT NULL DEFAULT 2 CHECK (priority IN (1,2,3)),
          status       TEXT NOT NULL DEFAULT 'todo'
                       CHECK (status IN ('todo','in_progress','done')),
          created_at   TEXT NOT NULL,
          updated_at   TEXT NOT NULL,
          completed_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_deadlines_due ON deadlines(due_at);
        PRAGMA user_version = 1;
        """
    )


# Порядок важен: миграция N переводит БД с user_version N-1 на N и сама ставит
# `PRAGMA user_version = N` (PRAGMA не принимает параметры, поэтому — литералом в SQL).
MIGRATIONS: list[Callable[[sqlite3.Connection], None]] = [_migration_1]


def migrate(conn: sqlite3.Connection) -> int:
    """Применяет недостающие миграции, возвращает итоговую версию схемы."""
    version: int = conn.execute("PRAGMA user_version").fetchone()[0]
    for number, migration in enumerate(MIGRATIONS, start=1):
        if number <= version:
            continue
        logger.info("applying migration %d", number)
        migration(conn)
        conn.commit()
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version != number:
            raise RuntimeError(f"migration {number} did not set user_version")
    return version


# --- Время -------------------------------------------------------------------

DUE_FORMAT = "%Y-%m-%dT%H:%M"
STAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


def now_stamp() -> str:
    """Текущее локальное время в формате служебных полей."""
    return datetime.now().strftime(STAMP_FORMAT)


def due_str(moment: datetime | None = None) -> str:
    """Момент (по умолчанию — сейчас) в формате due_at, пригодном для сравнения строк."""
    return (moment or datetime.now()).strftime(DUE_FORMAT)


# --- Типы ответов ------------------------------------------------------------


class Category(TypedDict):
    id: int
    name: str
    kind: str
    color: str
    created_at: str
    open_count: int


class Deadline(TypedDict):
    id: int
    title: str
    description: str
    due_at: str
    category_id: int | None
    priority: int
    status: str
    created_at: str
    updated_at: str
    completed_at: str | None
    is_overdue: bool


# --- Валидация ---------------------------------------------------------------

KINDS = ("study", "work", "other")
STATUSES = ("todo", "in_progress", "done")
PRIORITIES = (1, 2, 3)
COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}")
DUE_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")

Payload = Mapping[str, object]


def _check_fields(data: Payload, allowed: tuple[str, ...]) -> None:
    for key in data:
        if key not in allowed:
            raise ValidationError(key, f"Неизвестное поле «{key}»")


def _require(data: Payload, fields: tuple[str, ...]) -> None:
    for key in fields:
        if key not in data:
            raise ValidationError(key, "Обязательное поле")


def _text(data: Payload, field: str, min_len: int, max_len: int, strip: bool = True) -> str:
    value = data[field]
    if not isinstance(value, str):
        raise ValidationError(field, "Ожидается строка")
    if strip:
        value = value.strip()
    if not min_len <= len(value) <= max_len:
        if min_len > 0 and not value:
            raise ValidationError(field, "Поле не может быть пустым")
        raise ValidationError(field, f"Длина должна быть от {min_len} до {max_len} символов")
    return value


def _choice(data: Payload, field: str, choices: tuple[str, ...]) -> str:
    value = data[field]
    if not isinstance(value, str) or value not in choices:
        raise ValidationError(field, f"Допустимые значения: {', '.join(choices)}")
    return value


def _color(data: Payload) -> str:
    value = data["color"]
    if not isinstance(value, str) or not COLOR_RE.fullmatch(value):
        raise ValidationError("color", "Цвет должен быть в формате #rrggbb")
    return value.lower()


def _priority(data: Payload) -> int:
    value = data["priority"]
    # bool — подкласс int, его отсекаем явно.
    if isinstance(value, bool) or not isinstance(value, int) or value not in PRIORITIES:
        raise ValidationError("priority", "Приоритет должен быть 1, 2 или 3")
    return value


def _due_at(data: Payload) -> str:
    value = data["due_at"]
    if not isinstance(value, str) or not DUE_RE.fullmatch(value):
        raise ValidationError("due_at", "Дата должна быть в формате YYYY-MM-DDTHH:MM")
    try:
        datetime.strptime(value, DUE_FORMAT)
    except ValueError as err:
        raise ValidationError("due_at", "Несуществующая дата или время") from err
    return value


def _category_id(conn: sqlite3.Connection, data: Payload) -> int | None:
    value = data["category_id"]
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("category_id", "Ожидается id категории или null")
    if conn.execute("SELECT 1 FROM categories WHERE id = ?", (value,)).fetchone() is None:
        raise ValidationError("category_id", "Категория не найдена")
    return value


# --- Категории ---------------------------------------------------------------

CATEGORY_FIELDS = ("name", "kind", "color")

_CATEGORY_SELECT = """
    SELECT c.id, c.name, c.kind, c.color, c.created_at,
           (SELECT COUNT(*) FROM deadlines d
             WHERE d.category_id = c.id AND d.status != 'done') AS open_count
      FROM categories c
"""


def _category_from_row(row: sqlite3.Row) -> Category:
    return Category(
        id=row["id"],
        name=row["name"],
        kind=row["kind"],
        color=row["color"],
        created_at=row["created_at"],
        open_count=row["open_count"],
    )


def _validate_category(data: Payload) -> dict[str, object]:
    clean: dict[str, object] = {}
    if "name" in data:
        clean["name"] = _text(data, "name", 1, 60)
    if "kind" in data:
        clean["kind"] = _choice(data, "kind", KINDS)
    if "color" in data:
        clean["color"] = _color(data)
    return clean


def list_categories(conn: sqlite3.Connection) -> list[Category]:
    # COLLATE NOCASE в SQLite работает только для ASCII, поэтому сортируем в Python.
    rows = conn.execute(_CATEGORY_SELECT).fetchall()
    return sorted((_category_from_row(r) for r in rows), key=lambda c: (c["name"].casefold(), c["id"]))


def get_category(conn: sqlite3.Connection, category_id: int) -> Category:
    row = conn.execute(_CATEGORY_SELECT + " WHERE c.id = ?", (category_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Категория {category_id} не найдена")
    return _category_from_row(row)


def _ensure_unique_name(conn: sqlite3.Connection, name: str, exclude_id: int | None = None) -> None:
    """Проверка дубля без учёта регистра, включая кириллицу (NOCASE её не покрывает)."""
    folded = name.casefold()
    for row in conn.execute("SELECT id, name FROM categories"):
        if row["id"] != exclude_id and row["name"].casefold() == folded:
            raise ConflictError("Категория с таким именем уже существует", "name")


def _raise_if_name_conflict(err: sqlite3.IntegrityError) -> None:
    if "UNIQUE" in str(err) and "categories.name" in str(err):
        raise ConflictError("Категория с таким именем уже существует", "name") from err


def create_category(conn: sqlite3.Connection, data: Payload) -> Category:
    _check_fields(data, CATEGORY_FIELDS)
    _require(data, ("name", "kind"))
    clean = _validate_category(data)
    _ensure_unique_name(conn, str(clean["name"]))
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO categories (name, kind, color, created_at) VALUES (?, ?, ?, ?)",
                (clean["name"], clean["kind"], clean.get("color", "#888888"), now_stamp()),
            )
    except sqlite3.IntegrityError as err:
        _raise_if_name_conflict(err)
        raise
    assert cur.lastrowid is not None
    logger.info("category created id=%s", cur.lastrowid)
    return get_category(conn, cur.lastrowid)


def update_category(conn: sqlite3.Connection, category_id: int, data: Payload) -> Category:
    _check_fields(data, CATEGORY_FIELDS)
    current = get_category(conn, category_id)
    clean = _validate_category(data)
    if not clean:
        return current
    merged = {**current, **clean}
    _ensure_unique_name(conn, merged["name"], category_id)
    try:
        with conn:
            conn.execute(
                "UPDATE categories SET name = ?, kind = ?, color = ? WHERE id = ?",
                (merged["name"], merged["kind"], merged["color"], category_id),
            )
    except sqlite3.IntegrityError as err:
        _raise_if_name_conflict(err)
        raise
    return get_category(conn, category_id)


def delete_category(conn: sqlite3.Connection, category_id: int) -> None:
    with conn:
        cur = conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    if cur.rowcount == 0:
        raise NotFoundError(f"Категория {category_id} не найдена")
    logger.info("category deleted id=%s", category_id)


# --- Дедлайны ----------------------------------------------------------------

DEADLINE_FIELDS = ("title", "description", "due_at", "category_id", "priority", "status")


def _deadline_from_row(row: sqlite3.Row, now: str) -> Deadline:
    return Deadline(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        due_at=row["due_at"],
        category_id=row["category_id"],
        priority=row["priority"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
        is_overdue=row["status"] != "done" and row["due_at"] < now,
    )


def _validate_deadline(conn: sqlite3.Connection, data: Payload) -> dict[str, object]:
    clean: dict[str, object] = {}
    if "title" in data:
        clean["title"] = _text(data, "title", 1, 200)
    if "description" in data:
        clean["description"] = _text(data, "description", 0, 5000, strip=False)
    if "due_at" in data:
        clean["due_at"] = _due_at(data)
    if "category_id" in data:
        clean["category_id"] = _category_id(conn, data)
    if "priority" in data:
        clean["priority"] = _priority(data)
    if "status" in data:
        clean["status"] = _choice(data, "status", STATUSES)
    return clean


STATUS_FILTERS = (*STATUSES, "open")
# Значения — статические фрагменты SQL, выбираются по белому списку.
SORTS = {
    "due": "due_at, id",
    "priority": "priority DESC, due_at, id",
    "created": "created_at DESC, id DESC",
}
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class DeadlineFilter:
    """Разобранные параметры GET /api/deadlines (их же переиспользует экспорт .ics)."""

    status: str | None = None
    category_id: int | None = None
    without_category: bool = False
    q: str | None = None
    due_from: str | None = None  # 'YYYY-MM-DDTHH:MM', включительно
    due_to: str | None = None  # 'YYYY-MM-DDTHH:MM', включительно
    sort: str = "due"


def _parse_bound(query: Mapping[str, str], name: str, end_of_day: bool) -> str | None:
    value = query.get(name)
    if value is None or value == "":
        return None
    if DATE_RE.fullmatch(value):
        fmt = "%Y-%m-%d"
        bound = value + ("T23:59" if end_of_day else "T00:00")
    elif DUE_RE.fullmatch(value):
        fmt, bound = DUE_FORMAT, value
    else:
        raise ValidationError(name, "Ожидается YYYY-MM-DD или YYYY-MM-DDTHH:MM")
    try:
        datetime.strptime(value, fmt)
    except ValueError as err:
        raise ValidationError(name, "Несуществующая дата или время") from err
    return bound


def parse_deadline_filter(query: Mapping[str, str]) -> DeadlineFilter:
    """Валидирует query-параметры списка; ошибка — ValidationError(field=имя параметра).

    Неизвестные параметры игнорируются; пустое значение равно отсутствию параметра.
    """
    status = query.get("status") or None
    if status is not None and status not in STATUS_FILTERS:
        raise ValidationError("status", f"Допустимые значения: {', '.join(STATUS_FILTERS)}")
    category_id: int | None = None
    without_category = False
    raw_cat = query.get("category_id") or None
    if raw_cat == "none":
        without_category = True
    elif raw_cat is not None:
        if not raw_cat.isascii() or not raw_cat.isdigit():
            raise ValidationError("category_id", "Ожидается id категории или none")
        category_id = int(raw_cat)
    q = (query.get("q") or "").strip() or None
    if q is not None and len(q) > 200:
        raise ValidationError("q", "Слишком длинный запрос")
    due_from = _parse_bound(query, "from", end_of_day=False)
    due_to = _parse_bound(query, "to", end_of_day=True)
    if due_from is not None and due_to is not None and due_from > due_to:
        raise ValidationError("to", "Конец периода раньше начала")
    sort = query.get("sort") or "due"
    if sort not in SORTS:
        raise ValidationError("sort", f"Допустимые значения: {', '.join(SORTS)}")
    return DeadlineFilter(status, category_id, without_category, q, due_from, due_to, sort)


def list_deadlines(
    conn: sqlite3.Connection,
    filt: DeadlineFilter | None = None,
    now: datetime | None = None,
) -> list[Deadline]:
    """Список дедлайнов с фильтрами (AND) и сортировкой."""
    filt = filt or DeadlineFilter()
    where: list[str] = []
    params: list[object] = []
    if filt.status == "open":
        where.append("status != 'done'")
    elif filt.status is not None:
        where.append("status = ?")
        params.append(filt.status)
    if filt.without_category:
        where.append("category_id IS NULL")
    elif filt.category_id is not None:
        where.append("category_id = ?")
        params.append(filt.category_id)
    if filt.q is not None:
        where.append("(instr(py_casefold(title), ?) > 0 OR instr(py_casefold(description), ?) > 0)")
        params += [filt.q.casefold()] * 2
    if filt.due_from is not None:
        where.append("due_at >= ?")
        params.append(filt.due_from)
    if filt.due_to is not None:
        where.append("due_at <= ?")
        params.append(filt.due_to)
    sql = "SELECT * FROM deadlines"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY " + SORTS[filt.sort]
    now_s = due_str(now)
    return [_deadline_from_row(r, now_s) for r in conn.execute(sql, params).fetchall()]


class Stats(TypedDict):
    overdue: int
    today: int
    week: int
    open: int
    done: int


def stats(conn: sqlite3.Connection, now: datetime | None = None) -> Stats:
    """Сводка: overdue (<now), today (текущие сутки, вкл. просроченные сегодня),
    week ([now, now+7 суток]) — всё по не-done; open — не-done; done — выполненные."""
    now = now or datetime.now()
    now_s = due_str(now)
    day = now.strftime("%Y-%m-%d")
    row = conn.execute(
        """SELECT
             COALESCE(SUM(status != 'done' AND due_at < ?), 0)                  AS overdue,
             COALESCE(SUM(status != 'done' AND due_at BETWEEN ? AND ?), 0)      AS today,
             COALESCE(SUM(status != 'done' AND due_at BETWEEN ? AND ?), 0)      AS week,
             COALESCE(SUM(status != 'done'), 0)                                 AS open,
             COALESCE(SUM(status = 'done'), 0)                                  AS done
           FROM deadlines""",
        (now_s, day + "T00:00", day + "T23:59", now_s, due_str(now + timedelta(days=7))),
    ).fetchone()
    return Stats(
        overdue=row["overdue"], today=row["today"], week=row["week"],
        open=row["open"], done=row["done"],
    )


def get_deadline(
    conn: sqlite3.Connection, deadline_id: int, now: datetime | None = None
) -> Deadline:
    row = conn.execute("SELECT * FROM deadlines WHERE id = ?", (deadline_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Дедлайн {deadline_id} не найден")
    return _deadline_from_row(row, due_str(now))


def create_deadline(conn: sqlite3.Connection, data: Payload) -> Deadline:
    _check_fields(data, DEADLINE_FIELDS)
    _require(data, ("title", "due_at"))
    clean = _validate_deadline(conn, data)
    stamp = now_stamp()
    status = clean.get("status", "todo")
    with conn:
        cur = conn.execute(
            """INSERT INTO deadlines (title, description, due_at, category_id, priority,
                                      status, created_at, updated_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                clean["title"],
                clean.get("description", ""),
                clean["due_at"],
                clean.get("category_id"),
                clean.get("priority", 2),
                status,
                stamp,
                stamp,
                stamp if status == "done" else None,
            ),
        )
    assert cur.lastrowid is not None
    logger.info("deadline created id=%s", cur.lastrowid)
    return get_deadline(conn, cur.lastrowid)


def update_deadline(conn: sqlite3.Connection, deadline_id: int, data: Payload) -> Deadline:
    _check_fields(data, DEADLINE_FIELDS)
    current = get_deadline(conn, deadline_id)
    clean = _validate_deadline(conn, data)
    if not clean:
        return current
    stamp = now_stamp()
    new_status = clean.get("status", current["status"])
    if new_status == "done" and current["status"] != "done":
        clean["completed_at"] = stamp
    elif new_status != "done":
        clean["completed_at"] = None
    clean["updated_at"] = stamp
    m = {**current, **clean}
    with conn:
        conn.execute(
            """UPDATE deadlines SET title = ?, description = ?, due_at = ?, category_id = ?,
                                     priority = ?, status = ?, updated_at = ?, completed_at = ?
               WHERE id = ?""",
            (
                m["title"], m["description"], m["due_at"], m["category_id"], m["priority"],
                m["status"], m["updated_at"], m["completed_at"], deadline_id,
            ),
        )
    return get_deadline(conn, deadline_id)


def delete_deadline(conn: sqlite3.Connection, deadline_id: int) -> None:
    with conn:
        cur = conn.execute("DELETE FROM deadlines WHERE id = ?", (deadline_id,))
    if cur.rowcount == 0:
        raise NotFoundError(f"Дедлайн {deadline_id} не найден")
    logger.info("deadline deleted id=%s", deadline_id)
