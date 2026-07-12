"""Tests for row layout, insertion and batch formatting."""

from google_api.gsheet_writer import (
    build_format_requests,
    build_insert_rows_request,
    build_merge_requests,
    build_rows,
)

HEADERS = ["Status", "Order ID", "Title", "Total"]


def test_build_rows_maps_values_to_columns():
    items = [
        {"Order ID": "123", "Title": "Decal", "Total": 25.5},
        {"Order ID": "123", "Title": "Sticker", "Total": 25.5},
    ]
    rows = build_rows(items, HEADERS)
    assert rows == [
        ["", "123", "Decal", 25.5],
        ["", "123", "Sticker", 25.5],
    ]


def test_build_rows_ignores_unknown_keys_and_keeps_blanks():
    rows = build_rows([{"Order ID": "1", "No such column": "x"}], HEADERS)
    assert rows == [["", "1", "", ""]]


def test_build_insert_rows_request_exact_position():
    request = build_insert_rows_request(sheet_id=7, start_row_index=104, num_rows=2)
    dimension = request["insertDimension"]
    assert dimension["range"] == {
        "sheetId": 7,
        "dimension": "ROWS",
        "startIndex": 104,
        "endIndex": 106,
    }
    assert dimension["inheritFromBefore"] is False


def _kinds(requests):
    return [next(iter(request)) for request in requests]


def test_single_item_order_only_clip_and_status():
    requests = build_format_requests(
        sheet_id=7,
        start_row_index=104,
        num_rows=1,
        num_columns=len(HEADERS),
        highlight_col_indices=[1],
        status_col_index=0,
        rgb={"red": 1.0, "green": 0.5, "blue": 0.5},
    )
    assert _kinds(requests) == ["repeatCell", "repeatCell"]
    clip, status = requests
    assert clip["repeatCell"]["cell"]["userEnteredFormat"]["wrapStrategy"] == "CLIP"
    assert status["repeatCell"]["cell"]["userEnteredFormat"]["backgroundColor"] == {
        "red": 1.0,
        "green": 0.0,
        "blue": 0.0,
    }
    assert clip["repeatCell"]["range"]["startRowIndex"] == 104
    assert clip["repeatCell"]["range"]["endRowIndex"] == 105


def test_multi_item_order_adds_highlight():
    rgb = {"red": 0.55, "green": 0.8, "blue": 1.0}
    requests = build_format_requests(
        sheet_id=7,
        start_row_index=10,
        num_rows=3,
        num_columns=len(HEADERS),
        highlight_col_indices=[1, 2],
        status_col_index=0,
        rgb=rgb,
    )
    assert _kinds(requests) == ["repeatCell"] * 4
    highlight = requests[0]["repeatCell"]
    assert highlight["cell"]["userEnteredFormat"]["backgroundColor"] == rgb
    assert highlight["range"]["startRowIndex"] == 10
    assert highlight["range"]["endRowIndex"] == 13


def test_merge_requests_only_for_multi_item_orders():
    assert (
        build_merge_requests(
            sheet_id=7, start_row_index=10, num_rows=1, merge_col_indices=[3]
        )
        == []
    )

    requests = build_merge_requests(
        sheet_id=7, start_row_index=10, num_rows=3, merge_col_indices=[2, 3]
    )
    assert _kinds(requests) == ["mergeCells", "mergeCells"]
    merge = requests[0]["mergeCells"]
    assert merge["mergeType"] == "MERGE_ALL"
    assert merge["range"]["startRowIndex"] == 10
    assert merge["range"]["endRowIndex"] == 13
    assert merge["range"]["startColumnIndex"] == 2
    assert merge["range"]["endColumnIndex"] == 3
