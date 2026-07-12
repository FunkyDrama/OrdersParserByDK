"""GSheetWriter.append_order tests on a fake client: positional insertion
(like insert_row), request order and local free-row tracking."""

from unittest.mock import MagicMock, patch

import google_api.gsheet_writer as writer_module
from google_api.gsheet_writer import GSheetWriter

HEADERS = [
    "Status",
    "Additional Info",
    "Date",
    "Store",
    "Channel",
    "ASIN/SKU",
    "Listing Link",
    "Order ID",
    "Title",
    "Address/Ship to",
    "Quantity",
    "Customization info",
    "File Link",
    "Shipping label link",
    "Track ID",
    "Ship By",
    "Postal Service",
    "Shipping speed",
    "Track package",
    "Items total",
    "Shipping total",
    "Shipping price",
    "Total",
]


def _make_writer(existing_rows=104):
    """GSheetWriter with a fake worksheet holding existing_rows rows of data."""
    worksheet = MagicMock()
    worksheet.title = "22 roll"
    worksheet.id = 7
    worksheet.row_values.return_value = HEADERS
    worksheet.get_all_values.return_value = [["x"]] * existing_rows

    calls = []
    worksheet.spreadsheet.batch_update.side_effect = lambda body: calls.append(
        ("batch_update", body)
    )
    worksheet.update.side_effect = lambda values, range_name, **kw: calls.append(
        ("values_update", range_name, values, kw)
    )

    spreadsheet = MagicMock()
    spreadsheet.worksheet.return_value = worksheet

    client = MagicMock()
    client.open_by_key.return_value = spreadsheet

    settings = MagicMock()
    settings.TABLE_ID = "table"

    with (
        patch.object(writer_module, "get_gspread_client", return_value=client),
        patch.object(writer_module, "get_settings", return_value=settings),
    ):
        writer = GSheetWriter()
    return writer, worksheet, calls


def _order(n_items):
    return [
        {"Order ID": "A-1", "Title": f"Item {i}", "Customization info": ""}
        for i in range(n_items)
    ]


def test_single_item_positional_insert_two_requests():
    writer, worksheet, calls = _make_writer(existing_rows=104)

    writer.append_order(_order(1), "svg", 10.0)

    assert [c[0] for c in calls] == ["batch_update", "values_update"]

    requests = calls[0][1]["requests"]
    assert "insertDimension" in requests[0]
    dim = requests[0]["insertDimension"]["range"]
    assert (dim["startIndex"], dim["endIndex"]) == (104, 105)

    assert calls[1][1] == "A105"
    assert len(calls[1][2]) == 1
    assert calls[1][3]["value_input_option"] == "USER_ENTERED"


def test_multi_item_merges_go_after_values():
    writer, worksheet, calls = _make_writer(existing_rows=104)

    writer.append_order(_order(3), "svg", 10.0)

    assert [c[0] for c in calls] == ["batch_update", "values_update", "batch_update"]
    merge_requests = calls[2][1]["requests"]
    assert all("mergeCells" in r for r in merge_requests)
    assert len(merge_requests) == 7  # 7 merged columns
    assert merge_requests[0]["mergeCells"]["range"]["startRowIndex"] == 104
    assert merge_requests[0]["mergeCells"]["range"]["endRowIndex"] == 107


def test_next_row_tracked_locally_without_rereading_sheet():
    writer, worksheet, calls = _make_writer(existing_rows=104)

    writer.append_order(_order(2), "svg", 10.0)
    writer.append_order(_order(1), "svg", 10.0)

    assert worksheet.get_all_values.call_count == 1
    value_ranges = [c[1] for c in calls if c[0] == "values_update"]
    assert value_ranges == ["A105", "A107"]


def test_empty_order_writes_nothing():
    writer, worksheet, calls = _make_writer()
    writer.append_order([], "svg", 10.0)
    assert calls == []
