"""The order-processing pipeline: read → detect → parse → write."""

import traceback
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field


from core import console
from core.console import cprint
from core.i18n import tr
from core.dispatcher import detect_marketplace
from google_api.gdrive_finder import GoogleDriveFinder
from google_api.gsheet_writer import GSheetWriter


DEFAULT_MAX_WORKERS = 4


@dataclass
class OrderResult:
    """The outcome of a single order — feeds the summary and the Orders list in the UI."""

    number: int
    marketplace: str | None
    ok: bool
    order_id: str | None = None
    sheet: str | None = None
    items: int = 0
    error: str | None = None
    order_text: str = field(default="", repr=False)


@dataclass
class _ParsedOrder:
    """Intermediate result of the parsing phase (before the spreadsheet write)."""

    number: int
    order_text: str
    marketplace: str | None
    log_lines: list[str]
    order_data: list[dict] | None = None
    extension: str | None = None
    smaller_size: float | str | None = None
    customization: str | None = None
    error: str | None = None


def split_orders(orders_content: str) -> list[str]:
    """Splits the file into individual orders by </html>"""
    return [order for order in orders_content.split("</html>") if order.strip()]


def first_customization(order_data: list[dict]) -> str | None:
    """The first non-empty customization of the order to pick the Wallpaper sheet"""
    return next(
        (
            item["Customization info"]
            for item in order_data
            if item.get("Customization info")
        ),
        None,
    )


def _parse_one(number: int, order: str, finder: GoogleDriveFinder) -> _ParsedOrder:
    """The parsing phase of a single order (runs in a worker thread).

    All output is captured into a buffer and will be replayed by the
    pipeline in the original order of the orders.
    """
    with console.capture() as log_lines:
        spec = detect_marketplace(order)
        if spec is None:
            cprint(
                tr(
                    "||| Order {number}: marketplace not recognized, skipping |||",
                    number=number,
                ),
                "warning",
            )
            return _ParsedOrder(
                number, order, None, log_lines, error=tr("marketplace not recognized")
            )

        cprint(
            f"----- {tr('New order')} {spec.name} -----",
            level="header",
            style=spec.banner_style,
        )
        try:
            parser = spec.parser_cls(order, finder=finder)
            order_data = parser.parse_order()
            extension = parser.get_extension()
            smaller_size = parser.get_smaller_size()
            customization = first_customization(order_data)
            return _ParsedOrder(
                number,
                order,
                spec.name,
                log_lines,
                order_data=order_data,
                extension=extension,
                smaller_size=smaller_size,
                customization=customization,
            )
        except Exception as error:  # noqa: BLE001
            cprint(
                tr(
                    "||| Error processing the {name} order: {error} |||",
                    name=spec.name,
                    error=error,
                ),
                "error",
            )
            cprint(traceback.format_exc(), "error")
            return _ParsedOrder(number, order, spec.name, log_lines, error=str(error))


def process_order_list(
    orders: list[str],
    progress_callback: Callable[[int, int], None] | None = None,
    result_callback: Callable[[OrderResult], None] | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> tuple[int, int]:
    """Processes a list of orders."""
    total = len(orders)
    if total == 0:
        return 0, 0

    ok = 0
    failed = 0

    writer = GSheetWriter()
    finder = GoogleDriveFinder()

    workers = max(1, min(max_workers, total))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="parse") as pool:
        futures: list[Future[_ParsedOrder]] = [
            pool.submit(_parse_one, number, order, finder)
            for number, order in enumerate(orders, start=1)
        ]

        for future in futures:
            parsed = future.result()
            console.replay(parsed.log_lines)

            result = OrderResult(
                number=parsed.number,
                marketplace=parsed.marketplace,
                ok=False,
                order_text=parsed.order_text,
            )

            if parsed.error is not None:
                failed += 1
                result.error = parsed.error
            else:
                assert parsed.order_data is not None
                try:
                    sheet = writer.append_order(
                        parsed.order_data,
                        parsed.extension,  # type: ignore[arg-type]
                        parsed.smaller_size,  # type: ignore[arg-type]
                        parsed.customization,
                    )
                    ok += 1
                    result.ok = True
                    result.sheet = sheet
                    result.items = len(parsed.order_data)
                    result.order_id = next(
                        (
                            item.get("Order ID")
                            for item in parsed.order_data
                            if item.get("Order ID")
                        ),
                        None,
                    )
                except Exception as error:  # noqa: BLE001
                    failed += 1
                    result.error = str(error)
                    cprint(
                        tr(
                            "||| Error writing the {marketplace} order: {error} |||",
                            marketplace=parsed.marketplace,
                            error=error,
                        ),
                        "error",
                    )
                    cprint(traceback.format_exc(), "error")
                    cprint(
                        tr("||| Order skipped, moving on to the next one |||"),
                        "warning",
                    )

            if result_callback:
                result_callback(result)
            if progress_callback:
                progress_callback(parsed.number, total)

    return ok, failed


def process_orders(
    orders_content: str,
    progress_callback: Callable[[int, int], None] | None = None,
    result_callback: Callable[[OrderResult], None] | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> tuple[int, int]:
    """Processes all orders from the orders.txt content."""
    return process_order_list(
        split_orders(orders_content),
        progress_callback=progress_callback,
        result_callback=result_callback,
        max_workers=max_workers,
    )
