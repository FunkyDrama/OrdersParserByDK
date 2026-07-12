"""Path helpers: support running both as a script and as a packaged PyInstaller binary."""

import os
import sys


def resource_path(relative_path: str) -> str:
    """Path to a resource bundled into the executable (``_MEIPASS``) or living in the project."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def get_executable_dir() -> str:
    """Directory of the executable (frozen) or the project root."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_orders_file_path() -> str:
    """Path to orders.txt next to the executable (same as before)."""
    return os.path.join(get_executable_dir(), "orders.txt")
