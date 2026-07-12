"""Orders Parser entry point."""

import sys


from core.console import cprint
from core.i18n import set_language, tr
from core.constants import APP_VERSION
from core.paths import get_orders_file_path


def run_cli() -> None:
    """Console mode."""
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
    input(tr("Press Enter to exit..."))


def main() -> None:
    """Main function that starts the application"""
    from core.console import cleanup_old_logs

    cleanup_old_logs()

    if "--lang" in sys.argv:
        try:
            set_language(sys.argv[sys.argv.index("--lang") + 1])
        except IndexError:
            pass

    if "--cli" in sys.argv:
        run_cli()
    else:
        from ui.app import run_app

        run_app()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        cprint("\n" + tr("The program was interrupted by the user."), "error")
