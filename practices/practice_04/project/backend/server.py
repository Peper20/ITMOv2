"""HTTP-сервер «Сроки»: JSON API под /api и раздача статики фронтенда.

Запуск: `python3 backend/server.py` (конфиг через HOST/PORT/DB_PATH/FRONTEND_DIR).
Статика — сборка Vite (`frontend/dist`); без неё не-API пути отвечают страницей 503.
"""

from __future__ import annotations

import html
import json
import logging
import mimetypes
import os
import re
import sqlite3
from collections.abc import Callable
from contextlib import closing
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

try:  # импорт как пакет `backend.server` (тесты)
    from . import db
except ImportError:  # запуск скриптом: python3 backend/server.py
    import db

logger = logging.getLogger("sroki.server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_VERSION = "1"
MAX_BODY = 1024 * 1024
DEFAULT_FRONTEND_DIR = "frontend/dist"
BUILD_HINT = "cd frontend && npm ci && npm run build"

# --- Конфигурация ------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    db_path: Path
    frontend_dir: Path

    @classmethod
    def from_env(cls) -> Config:
        def project_path(value: str) -> Path:
            path = Path(value)
            return path if path.is_absolute() else PROJECT_ROOT / path

        return cls(
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "8000")),
            db_path=project_path(os.environ.get("DB_PATH", "data/app.db")),
            frontend_dir=project_path(os.environ.get("FRONTEND_DIR", DEFAULT_FRONTEND_DIR)),
        )


# --- Ответы и ошибки ---------------------------------------------------------


class HttpError(Exception):
    """Ошибка протокольного уровня (невалидный JSON, 404 маршрута, 405)."""

    def __init__(self, status: HTTPStatus, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.field = field


@dataclass
class Response:
    status: HTTPStatus
    body: object = None  # JSON-сериализуемое; bytes отдаются как есть; None + 204 → без тела
    content_type: str = "application/octet-stream"  # только для bytes
    headers: dict[str, str] = field(default_factory=dict[str, str])


@dataclass
class Request:
    conn: sqlite3.Connection
    params: dict[str, int]  # именованные группы из пути (id)
    query: dict[str, str]  # query string (последнее значение каждого параметра)
    body: dict[str, object]
    now: datetime  # «сейчас» для is_overdue/stats; в тестах подменяется через App.clock


Handler = Callable[[Request], Response]

# --- Обработчики API ---------------------------------------------------------


def health(_req: Request) -> Response:
    return Response(HTTPStatus.OK, {"status": "ok", "version": API_VERSION})


def list_categories(req: Request) -> Response:
    return Response(HTTPStatus.OK, db.list_categories(req.conn))


def create_category(req: Request) -> Response:
    return Response(HTTPStatus.CREATED, db.create_category(req.conn, req.body))


def update_category(req: Request) -> Response:
    return Response(HTTPStatus.OK, db.update_category(req.conn, req.params["id"], req.body))


def delete_category(req: Request) -> Response:
    db.delete_category(req.conn, req.params["id"])
    return Response(HTTPStatus.NO_CONTENT)


def list_deadlines(req: Request) -> Response:
    filt = db.parse_deadline_filter(req.query)
    return Response(HTTPStatus.OK, db.list_deadlines(req.conn, filt, req.now))


def get_stats(req: Request) -> Response:
    return Response(HTTPStatus.OK, db.stats(req.conn, req.now))


def export_ics(req: Request) -> Response:
    filt = db.parse_deadline_filter(req.query)
    if filt.status is None:  # по умолчанию в календарь попадают только не-done
        filt = replace(filt, status="open")
    deadlines = db.list_deadlines(req.conn, filt, req.now)
    names = {c["id"]: c["name"] for c in db.list_categories(req.conn)}
    return Response(
        HTTPStatus.OK,
        build_ics(deadlines, names, req.now).encode("utf-8"),
        content_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="deadlines.ics"'},
    )


def create_deadline(req: Request) -> Response:
    return Response(HTTPStatus.CREATED, db.create_deadline(req.conn, req.body))


def get_deadline(req: Request) -> Response:
    return Response(HTTPStatus.OK, db.get_deadline(req.conn, req.params["id"], req.now))


def update_deadline(req: Request) -> Response:
    return Response(HTTPStatus.OK, db.update_deadline(req.conn, req.params["id"], req.body))


def delete_deadline(req: Request) -> Response:
    db.delete_deadline(req.conn, req.params["id"])
    return Response(HTTPStatus.NO_CONTENT)


# Путь (regex с именованными группами) → {метод: обработчик}.
ROUTES: list[tuple[re.Pattern[str], dict[str, Handler]]] = [
    (re.compile(r"/api/health"), {"GET": health}),
    (re.compile(r"/api/categories"), {"GET": list_categories, "POST": create_category}),
    (
        re.compile(r"/api/categories/(?P<id>\d+)"),
        {"PATCH": update_category, "DELETE": delete_category},
    ),
    (re.compile(r"/api/deadlines"), {"GET": list_deadlines, "POST": create_deadline}),
    (re.compile(r"/api/stats"), {"GET": get_stats}),
    (re.compile(r"/api/export\.ics"), {"GET": export_ics}),
    (
        re.compile(r"/api/deadlines/(?P<id>\d+)"),
        {"GET": get_deadline, "PATCH": update_deadline, "DELETE": delete_deadline},
    ),
]

BODY_METHODS = ("POST", "PATCH")


def resolve_route(method: str, path: str) -> tuple[Handler, dict[str, int]]:
    for pattern, methods in ROUTES:
        match = pattern.fullmatch(path)
        if match is None:
            continue
        handler = methods.get(method)
        if handler is None:
            raise HttpError(HTTPStatus.METHOD_NOT_ALLOWED, "Метод не поддерживается")
        return handler, {k: int(v) for k, v in match.groupdict().items()}
    raise HttpError(HTTPStatus.NOT_FOUND, "Ресурс не найден")


def allowed_methods(path: str) -> list[str]:
    for pattern, methods in ROUTES:
        if pattern.fullmatch(path):
            return sorted(methods)
    return []


# --- iCalendar (RFC 5545) ----------------------------------------------------

ICS_EVENT_MINUTES = 30  # DTEND = DTSTART + 30 мин (DTEND должен быть позже DTSTART)
ICS_PRIORITY = {3: 1, 2: 5, 1: 9}  # наш приоритет → PRIORITY (1 — высший, 9 — низший)


def ics_escape(text: str) -> str:
    """Экранирование TEXT-значения: \\ ; , и переводы строк (RFC 5545, 3.3.11)."""
    text = text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return text.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")


def ics_fold(line: str, limit: int = 75) -> str:
    """Свёртка строки до `limit` октетов UTF-8, не разрывая символы (RFC 5545, 3.1).

    Продолжения начинаются с пробела, который тоже входит в лимит строки.
    """
    parts: list[str] = []
    current: list[str] = []
    size = 0
    for char in line:
        width = len(char.encode("utf-8"))
        if size + width > limit:
            parts.append("".join(current))
            current, size = [" "], 1
        current.append(char)
        size += width
    parts.append("".join(current))
    return "\r\n".join(parts)


def _ics_local(due_at: str, delta: timedelta = timedelta()) -> str:
    """'YYYY-MM-DDTHH:MM' → floating local DATE-TIME 'YYYYMMDDTHHMMSS'."""
    return (datetime.strptime(due_at, db.DUE_FORMAT) + delta).strftime("%Y%m%dT%H%M%S")


def build_ics(deadlines: Iterable[db.Deadline], categories: dict[int, str], now: datetime) -> str:
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Sroki//Deadline tracker//RU",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Сроки",
    ]
    for dl in deadlines:
        lines += [
            "BEGIN:VEVENT",
            f"UID:deadline-{dl['id']}@sroki",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{_ics_local(dl['due_at'])}",
            f"DTEND:{_ics_local(dl['due_at'], timedelta(minutes=ICS_EVENT_MINUTES))}",
            f"SUMMARY:{ics_escape(dl['title'])}",
            f"PRIORITY:{ICS_PRIORITY[dl['priority']]}",
        ]
        if dl["description"]:
            lines.append(f"DESCRIPTION:{ics_escape(dl['description'])}")
        category = categories.get(dl["category_id"]) if dl["category_id"] is not None else None
        if category is not None:
            lines.append(f"CATEGORIES:{ics_escape(category)}")
        if dl["status"] == "done":
            lines.append("STATUS:COMPLETED")  # только если явно запрошены done
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "".join(ics_fold(line) + "\r\n" for line in lines)


# --- Статика -----------------------------------------------------------------

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",  # ES-модули Vite: браузер требует JS MIME
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8",  # source maps
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".webp": "image/webp",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".txt": "text/plain; charset=utf-8",
}

# Vite кладёт в assets/ файлы с хэшем содержимого в имени — их можно кэшировать навсегда.
IMMUTABLE_DIR = "assets"
CACHE_IMMUTABLE = "public, max-age=31536000, immutable"
CACHE_REVALIDATE = "no-cache"


def frontend_ready(frontend_dir: Path) -> bool:
    """Есть ли собранный фронтенд (index.html в каталоге статики)."""
    return (frontend_dir / "index.html").is_file()


def cache_control(frontend_dir: Path, target: Path) -> str:
    """immutable для файлов под assets/, no-cache для остального (index.html и т. п.)."""
    rel = target.relative_to(frontend_dir.resolve())
    return CACHE_IMMUTABLE if rel.parts[0] == IMMUTABLE_DIR and len(rel.parts) > 1 else CACHE_REVALIDATE


def build_missing_page(frontend_dir: Path) -> bytes:
    """HTML-страница 503 «фронтенд не собран» с подсказкой, как его собрать."""
    page = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Сроки — фронтенд не собран</title>
<style>
body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 40rem; margin: 4rem auto; padding: 0 1rem; }}
code, pre {{ font-family: ui-monospace, monospace; }}
pre {{ background: #f2f2f2; padding: .75rem 1rem; border-radius: 6px; overflow-x: auto; }}
</style>
</head>
<body>
<h1>Фронтенд не собран</h1>
<p>Сервер работает, API доступно по <code>/api</code>, но в каталоге
<code>{html.escape(str(frontend_dir))}</code> нет <code>index.html</code>.</p>
<p>Соберите фронтенд из корня проекта и обновите страницу:</p>
<pre>{html.escape(BUILD_HINT)}</pre>
<p>Другой каталог сборки можно указать через переменную <code>FRONTEND_DIR</code>.</p>
</body>
</html>
"""
    return page.encode("utf-8")


def resolve_static(frontend_dir: Path, url_path: str) -> Path | None:
    """Возвращает файл внутри frontend_dir или None (нет файла / выход за пределы)."""
    rel = unquote(url_path).lstrip("/") or "index.html"
    root = frontend_dir.resolve()
    target = (root / rel).resolve()
    if not target.is_relative_to(root):
        return None
    if target.is_dir():
        target = target / "index.html"
    return target if target.is_file() else None


def content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in CONTENT_TYPES:
        return CONTENT_TYPES[suffix]
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


# --- HTTP --------------------------------------------------------------------


def recover_utf8(text: str) -> str:
    """Чинит сырые UTF-8 байты в строке запроса.

    http.server декодирует строку запроса как latin-1, поэтому `тест`, отправленный
    байтами, превращается в «ÑÐµÑÑ». Восстанавливаем байты и декодируем их как UTF-8
    (битые последовательности заменяются на U+FFFD). Percent-escapes не трогаем.
    """
    try:
        return text.encode("latin-1").decode("utf-8", errors="replace")
    except UnicodeEncodeError:
        return text  # строка не из сырых байт (уже нормальный Unicode)


def readable_for_log(text: str) -> str:
    """Строка запроса для лога: UTF-8, раскодированные percent-escapes, экранированные
    управляющие символы (чтобы `%0A` и подобное не подделывали строки лога)."""
    text = unquote(recover_utf8(text), errors="replace")
    return "".join(c if c.isprintable() else c.encode("unicode_escape").decode("ascii") for c in text)



class App(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, config: Config, clock: Callable[[], datetime] = datetime.now) -> None:
        self.config = config
        self.clock = clock
        with closing(db.connect(config.db_path)) as conn:
            db.migrate(conn)
        if not frontend_ready(config.frontend_dir):
            logger.warning(
                "frontend build not found in %s (no index.html): non-API paths will return 503; run: %s",
                config.frontend_dir,
                BUILD_HINT,
            )
        super().__init__((config.host, config.port), RequestHandler)


class RequestHandler(BaseHTTPRequestHandler):
    server: App  # pyright: ignore[reportIncompatibleVariableOverride]  # уточняем тип
    server_version = "Sroki/" + API_VERSION

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        safe = tuple(readable_for_log(a) if isinstance(a, str) else a for a in args)
        logger.info("%s - %s", self.address_string(), format % safe)

    def do_GET(self) -> None:
        self.dispatch("GET")

    def do_HEAD(self) -> None:
        self.dispatch("HEAD")

    def do_POST(self) -> None:
        self.dispatch("POST")

    def do_PATCH(self) -> None:
        self.dispatch("PATCH")

    def do_DELETE(self) -> None:
        self.dispatch("DELETE")

    def do_PUT(self) -> None:
        self.dispatch("PUT")

    # --- диспетчеризация ---

    def dispatch(self, method: str) -> None:
        url = urlsplit(recover_utf8(self.path))  # сырые UTF-8 байты == percent-encoding
        if url.path == "/api" or url.path.startswith("/api/"):
            self.handle_api(method, url.path, url.query)
        else:
            self.handle_static(method, url.path)

    def handle_api(self, method: str, path: str, raw_query: str) -> None:
        try:
            handler, params = resolve_route(method, path)
            body = self.read_json() if method in BODY_METHODS else {}
            query = {k: v[-1] for k, v in parse_qs(raw_query).items()}
            with closing(db.connect(self.server.config.db_path)) as conn:
                response = handler(Request(conn, params, query, body, self.server.clock()))
        except HttpError as err:
            headers = {}
            if err.status == HTTPStatus.METHOD_NOT_ALLOWED:
                headers["Allow"] = ", ".join(allowed_methods(path))
            self.send_error_json(err.status, err.message, err.field, headers)
        except db.ValidationError as err:
            self.send_error_json(HTTPStatus.BAD_REQUEST, err.message, err.field)
        except db.NotFoundError as err:
            self.send_error_json(HTTPStatus.NOT_FOUND, str(err))
        except db.ConflictError as err:
            self.send_error_json(HTTPStatus.CONFLICT, err.message, err.field)
        except Exception:
            logger.exception("unhandled error: %s %s", method, self.path)
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "Внутренняя ошибка сервера")
        else:
            if isinstance(response.body, bytes):
                self.send_payload(response.status, response.body, response.content_type, response.headers)
            else:
                self.send_json(response.status, response.body, response.headers)

    def read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError as err:
            raise HttpError(HTTPStatus.BAD_REQUEST, "Некорректный Content-Length") from err
        if length <= 0:
            raise HttpError(HTTPStatus.BAD_REQUEST, "Пустое тело запроса, ожидается JSON")
        if length > MAX_BODY:
            # Тело не читаем — соединение после ответа закрывается.
            self.close_connection = True
            raise HttpError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Слишком большое тело запроса (максимум 1 МБ)")
        raw = self.rfile.read(length)
        try:
            data: object = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise HttpError(HTTPStatus.BAD_REQUEST, "Невалидный JSON") from err
        if not isinstance(data, dict):
            raise HttpError(HTTPStatus.BAD_REQUEST, "Ожидается JSON-объект")
        return {str(k): v for k, v in data.items()}  # pyright: ignore[reportUnknownVariableType]

    def handle_static(self, method: str, path: str) -> None:
        if method not in ("GET", "HEAD"):
            self.send_error_json(
                HTTPStatus.METHOD_NOT_ALLOWED, "Метод не поддерживается", headers={"Allow": "GET, HEAD"}
            )
            return
        frontend_dir = self.server.config.frontend_dir
        if not frontend_ready(frontend_dir):  # проверяем на каждый запрос: сборка может появиться без рестарта
            self.send_payload(
                HTTPStatus.SERVICE_UNAVAILABLE,
                build_missing_page(frontend_dir),
                "text/html; charset=utf-8",
                {"Cache-Control": "no-store"},
            )
            return
        target = resolve_static(frontend_dir, path)
        if target is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Файл не найден")
            return
        self.send_payload(
            HTTPStatus.OK,
            target.read_bytes(),
            content_type(target),
            {"Cache-Control": cache_control(frontend_dir, target)},
        )

    # --- отправка ---

    def send_json(
        self, status: HTTPStatus, body: object, headers: dict[str, str] | None = None
    ) -> None:
        if status == HTTPStatus.NO_CONTENT:
            self.send_payload(status, b"", None, headers)
            return
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_payload(status, payload, "application/json; charset=utf-8", headers)

    def send_payload(
        self,
        status: HTTPStatus,
        payload: bytes,
        content_type: str | None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Отправляет готовое тело; для HEAD — только заголовки."""
        self.send_response(status)
        if content_type is not None:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def send_error_json(
        self,
        status: HTTPStatus,
        message: str,
        field: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        body: dict[str, str] = {"error": message}
        if field is not None:
            body["field"] = field
        self.send_json(status, body, headers)


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = Config.from_env()
    server = App(config)
    host, port = server.server_address[:2]
    logger.info("listening on http://%s:%s (db=%s)", host, port, config.db_path)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
