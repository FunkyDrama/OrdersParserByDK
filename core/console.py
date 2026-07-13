"""The single output point for all messages."""

import logging
import os
import re
import sys
import threading
from contextlib import contextmanager
from datetime import date
from collections.abc import Callable, Iterator
from typing import Literal

from colorama import Fore, Style
from colorama import init as colorama_init

from core.paths import get_logs_dir

colorama_init(autoreset=True)

Level = Literal["info", "success", "warning", "error", "header"]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

_COLOR_BY_LEVEL: dict[Level, str] = {
    "info": "",
    "success": Fore.GREEN,
    "warning": Fore.YELLOW,
    "error": Fore.RED,
    "header": Fore.CYAN,
}

_subscribers: list[Callable[[str, Level], None]] = []
_lock = threading.Lock()
_logger: logging.Logger | None = None


def subscribe(callback: Callable[[str, Level], None]) -> None:
    """Subscribes a handler (ANSI-free text, level). Used by the UI."""
    with _lock:
        _subscribers.append(callback)


def unsubscribe(callback: Callable[[str, Level], None]) -> None:
    with _lock:
        if callback in _subscribers:
            _subscribers.remove(callback)


_LOG_NAME_RE = re.compile(r"^parser_(\d{4}-\d{2}-\d{2})\.log$")


def cleanup_old_logs(
    log_dir: str | None = None,
    max_age_days: int | None = None,
    today: date | None = None,
) -> int:
    """Deletes logs older than max_age_days (based on the date in the filename).

    Called at application startup; touches only files named
    parser_YYYY-MM-DD.log inside the logs folder. Returns the number of
    deleted files. Any filesystem errors are silently ignored — the cleanup
    must never get in the way of the application.
    """
    from core.constants import LOG_RETENTION_DAYS

    if max_age_days is None:
        max_age_days = LOG_RETENTION_DAYS
    if log_dir is None:
        log_dir = get_logs_dir()
    if not os.path.isdir(log_dir):
        return 0

    current = today or date.today()
    deleted = 0
    try:
        names = os.listdir(log_dir)
    except OSError:
        return 0

    for name in names:
        match = _LOG_NAME_RE.match(name)
        if not match:
            continue
        try:
            file_date = date.fromisoformat(match.group(1))
        except ValueError:
            continue
        if (current - file_date).days > max_age_days:
            try:
                os.remove(os.path.join(log_dir, name))
                deleted += 1
            except OSError:
                pass
    return deleted


def _get_logger() -> logging.Logger:
    """Lazy initialization of the file log next to the executable."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("orders_parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        log_dir = get_logs_dir()
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"parser_{date.today():%Y-%m-%d}.log")
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())
    _logger = logger
    return logger


_capture_ctx = threading.local()


@contextmanager
def capture() -> Iterator[list[str]]:
    """Captures all cprint output of the current thread into a list of raw lines.."""
    buffer: list[str] = []
    previous = getattr(_capture_ctx, "buffer", None)
    _capture_ctx.buffer = buffer
    try:
        yield buffer
    finally:
        _capture_ctx.buffer = previous


def replay(raw_lines: list[str]) -> None:
    """Replays captured lines: console, log file and subscribers."""
    for raw in raw_lines:
        if ":" in raw:
            level_tag, _, text = raw.partition(":")
            if level_tag in _COLOR_BY_LEVEL:
                _emit(text, level=level_tag)  # type: ignore[arg-type]
                continue
        _emit(raw)


def cprint(
    *args: object,
    sep: str = " ",
    end: str = "\n",
    level: Level = "info",
    style: str | None = None,
) -> None:
    """Prints to the console (with colors) and mirrors the message to the log and subscribers.

    ``level`` controls the terminal color and what subscribers receive:
      - "success"  → green
      - "warning"  → yellow
      - "error"    → red
      - "header"   → cyan
      - "info"     → default (no color)

    ``style`` overrides the terminal color without affecting the level sent to
    subscribers (useful for per-marketplace banner colors).

    Callers may pass the level as the last positional argument for brevity:
    ``cprint("msg", "success")`` is equivalent to ``cprint("msg", level="success")``.

    If capture() is active in the current thread, the line goes into the
    buffer and is emitted later via replay() — in the correct order.
    """
    if args and isinstance(args[-1], str) and args[-1] in _COLOR_BY_LEVEL:
        level = args[-1]  # type: ignore[assignment]
        args = args[:-1]
    text = sep.join(str(a) for a in args)

    buffer = getattr(_capture_ctx, "buffer", None)
    if buffer is not None:
        # Store as "level:text" for replay()
        buffer.append(f"{level}:{text}")
        return

    _emit(text, level=level, end=end, style=style)


def _emit(
    text: str, level: Level = "info", end: str = "\n", style: str | None = None
) -> None:
    plain = _ANSI_RE.sub("", text).rstrip()

    if sys.stdout is not None:
        try:
            color = style if style is not None else _COLOR_BY_LEVEL.get(level, "")
            sys.stdout.write(color + plain + (Style.RESET_ALL if color else "") + end)
            sys.stdout.flush()
        except (OSError, ValueError):
            pass

    if not plain:
        return

    _get_logger().info(plain)

    with _lock:
        subscribers = list(_subscribers)
    for callback in subscribers:
        try:
            callback(plain, level)
        except Exception:  # noqa: BLE001
            pass
