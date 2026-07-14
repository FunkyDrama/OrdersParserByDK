"""Windowed CLI entry point for Windows Server builds."""

import sys

from core.cli import run_cli
from core.console import cleanup_old_logs, cprint
from core.i18n import set_language, tr


def main() -> None:
    """Run the order processor without importing the desktop UI."""
    cleanup_old_logs()

    if "--lang" in sys.argv:
        try:
            set_language(sys.argv[sys.argv.index("--lang") + 1])
        except IndexError:
            pass

    run_cli()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        cprint("\n" + tr("The program was interrupted by the user."), "error")
