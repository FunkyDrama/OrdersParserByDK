"""CLI runner shared by source runs and the Windows Server build."""

import sys

from core.console import cprint
from core.constants import APP_VERSION
from core.i18n import tr
from core.paths import get_orders_file_path


def run_cli(*, wait_for_enter: bool = True) -> None:
    """Process orders from orders.txt without starting the desktop UI."""
    from core.processor import process_orders

    cprint(f"---Orders Parser v{APP_VERSION} by Daniel K---", "header")

    orders_path = get_orders_file_path()
    try:
        with open(orders_path, "r", encoding="utf-8") as f:
            orders_content = f.read()
    except FileNotFoundError:
        cprint(tr("File {path} not found.", path=orders_path))
        return

    ok, failed = process_orders(orders_content)

    cprint(
        tr(
            "<-- All data added successfully. Please double-check the data in the spreadsheet! -->"
        ),
        "header",
    )
    if failed:
        cprint(
            tr(
                "Warning: {failed} order(s) skipped due to errors, written: {ok}.",
                failed=failed,
                ok=ok,
            ),
            "warning",
        )

    if wait_for_enter and sys.stdin is not None:
        try:
            input(tr("Press Enter to exit..."))
        except (EOFError, RuntimeError):
            pass
