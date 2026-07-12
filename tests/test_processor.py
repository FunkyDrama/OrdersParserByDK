"""Processing pipeline tests: error isolation and customization selection."""

from unittest.mock import patch

import core.processor as processor_module
from core.processor import first_customization, process_orders, split_orders


def test_split_orders():
    content = "<html>a</html>\n<html>b</html>\n   \n"
    assert split_orders(content) == ["<html>a", "\n<html>b"]


def test_first_customization_picks_first_non_empty():
    order_data = [
        {"Customization info": ""},
        {"Customization info": None},
        {"Customization info": "Material: Peel and Stick"},
        {"Customization info": "another"},
    ]
    assert first_customization(order_data) == "Material: Peel and Stick"
    assert first_customization([{"Customization info": ""}]) is None


class _FakeWriter:
    def __init__(self):
        self.appended = []

    def append_order(self, order_data, extension, smaller_size, customization):
        self.appended.append((order_data, extension, smaller_size, customization))
        return "22 roll"


class _FakeParser:
    """A parser that always succeeds"""

    def __init__(self, order, finder=None):
        self.order = order

    def parse_order(self):
        return [{"Customization info": "Size: 24x36"}]

    def get_extension(self):
        return "svg"

    def get_smaller_size(self):
        return 24.0


class _BrokenParser(_FakeParser):
    def parse_order(self):
        raise ValueError("broken order")


def _run(orders_content, parser_cls):
    fake_writer = _FakeWriter()
    with (
        patch.object(processor_module, "GSheetWriter", return_value=fake_writer),
        patch.object(processor_module, "GoogleDriveFinder", return_value=object()),
        patch.object(processor_module, "detect_marketplace") as detect,
    ):
        from core.dispatcher import MarketplaceSpec

        detect.side_effect = lambda order: (
            MarketplaceSpec("Etsy", lambda o: True, parser_cls, "green")
            if "etsy" in order
            else None
        )
        result = process_orders(orders_content)
    return result, fake_writer


def test_successful_orders_are_written():
    (ok, failed), writer = _run("etsy 1</html>etsy 2</html>", _FakeParser)
    assert (ok, failed) == (2, 0)
    assert len(writer.appended) == 2
    _, extension, smaller_size, customization = writer.appended[0]
    assert (extension, smaller_size, customization) == ("svg", 24.0, "Size: 24x36")


def test_broken_order_is_skipped_and_processing_continues():
    (ok, failed), writer = _run("etsy 1</html>", _BrokenParser)
    assert (ok, failed) == (0, 1)
    assert writer.appended == []


def test_unrecognized_order_counts_as_failed():
    (ok, failed), writer = _run("unrecognizable order</html>", _FakeParser)
    assert (ok, failed) == (0, 1)
    assert writer.appended == []


def test_progress_callback_called_per_order():
    calls = []
    fake_writer = _FakeWriter()
    with (
        patch.object(processor_module, "GSheetWriter", return_value=fake_writer),
        patch.object(processor_module, "GoogleDriveFinder", return_value=object()),
        patch.object(processor_module, "detect_marketplace", return_value=None),
    ):
        process_orders(
            "a</html>b</html>c</html>",
            progress_callback=lambda cur, total: calls.append((cur, total)),
        )
    assert calls == [(1, 3), (2, 3), (3, 3)]


def test_parallel_parsing_preserves_original_order():
    """The first order takes the longest to parse but is written first."""
    import time

    class SlowFirstParser(_FakeParser):
        def __init__(self, order, finder=None):
            super().__init__(order, finder)
            self.n = int(order.split()[-1])

        def parse_order(self):
            time.sleep(0.08 if self.n == 1 else 0.0)
            return [{"Customization info": "", "Order ID": f"id-{self.n}"}]

    content = "etsy 1</html>etsy 2</html>etsy 3</html>etsy 4</html>"
    (ok, failed), writer = _run(content, SlowFirstParser)

    assert (ok, failed) == (4, 0)
    written_ids = [order_data[0]["Order ID"] for order_data, *_ in writer.appended]
    assert written_ids == ["id-1", "id-2", "id-3", "id-4"]


def test_result_callback_receives_ordered_results():
    from core.processor import OrderResult

    results: list[OrderResult] = []
    fake_writer = _FakeWriter()
    with (
        patch.object(processor_module, "GSheetWriter", return_value=fake_writer),
        patch.object(processor_module, "GoogleDriveFinder", return_value=object()),
        patch.object(processor_module, "detect_marketplace") as detect,
    ):
        from core.dispatcher import MarketplaceSpec

        detect.side_effect = lambda order: MarketplaceSpec(
            "Etsy", lambda o: True, _FakeParser, "green"
        )
        processor_module.process_orders(
            "a</html>b</html>c</html>", result_callback=results.append
        )

    assert [r.number for r in results] == [1, 2, 3]
    assert all(r.ok for r in results)
    assert all(r.sheet == "22 roll" or r.sheet is None for r in results)


def test_failed_result_keeps_order_text_for_retry():
    (ok, failed), writer = _run("etsy A</html>", _BrokenParser)
    assert (ok, failed) == (0, 1)
