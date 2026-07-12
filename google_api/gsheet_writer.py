"""Writing orders to Google Sheets."""

import random
from typing import Any

from gspread import Spreadsheet, Worksheet
from gspread.utils import ValueInputOption

from config.settings import get_settings
from core.console import cprint
from core.i18n import tr
from core.constants import (
    COL_STATUS,
    COLORED_EXTENSIONS,
    HIGHLIGHT_COLUMNS,
    MERGE_COLUMNS,
    MULTI_ITEM_PALETTE,
    ROLL_SIZE_THRESHOLD,
    SHEET_22_ROLL,
    SHEET_46_ROLL,
    SHEET_COLORED,
    SHEET_ERROR,
    SHEET_WALLPAPER,
    STATUS_CELL_COLOR,
    WALLPAPER_PATTERN,  # noqa: F401
)
from google_api.auth import get_gspread_client


def select_sheet_name(
    extension: str,
    smaller_size: float | str,
    customization_info: str | None = None,
) -> str:
    """Picks the sheet based on customization, file extension and the smaller side."""
    if customization_info and WALLPAPER_PATTERN.search(customization_info):
        return SHEET_WALLPAPER

    if extension != "Unknown":
        if extension in COLORED_EXTENSIONS:
            return SHEET_COLORED
        if isinstance(smaller_size, float):
            if smaller_size <= ROLL_SIZE_THRESHOLD:
                return SHEET_22_ROLL
            return SHEET_46_ROLL

    return SHEET_ERROR


def build_rows(
    order_items: list[dict[str, None | str | int]], headers: list[str]
) -> list[list[Any]]:
    """Lays out the order dicts across the sheet columns."""
    header_index = {name: idx for idx, name in enumerate(headers)}
    rows: list[list[Any]] = []
    for order_item in order_items:
        row_data: list[Any] = ["" for _ in range(len(headers))]
        for column, value in order_item.items():
            col_index = header_index.get(column)
            if col_index is not None:
                row_data[col_index] = value
        rows.append(row_data)
    return rows


def build_insert_rows_request(
    sheet_id: int, start_row_index: int, num_rows: int
) -> dict[str, Any]:
    """insertDimension: blank rows at the exact position."""
    return {
        "insertDimension": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": start_row_index,
                "endIndex": start_row_index + num_rows,
            },
            "inheritFromBefore": False,
        }
    }


def build_format_requests(
    sheet_id: int,
    start_row_index: int,
    num_rows: int,
    num_columns: int,
    highlight_col_indices: list[int],
    status_col_index: int,
    rgb: dict[str, float],
) -> list[dict[str, Any]]:
    """Order formatting: 4 highlighted columns for multi-item orders,
    CLIP across the whole row and a red Status — always.

    Cell merges are collected separately (build_merge_requests) because
    they run after the values are written.
    """
    end_row_index = start_row_index + num_rows
    requests: list[dict[str, Any]] = []

    if num_rows > 1:
        for col in highlight_col_indices:
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row_index,
                            "endRowIndex": end_row_index,
                            "startColumnIndex": col,
                            "endColumnIndex": col + 1,
                        },
                        "cell": {"userEnteredFormat": {"backgroundColor": rgb}},
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                }
            )

    requests.append(
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row_index,
                    "endRowIndex": end_row_index,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_columns,
                },
                "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP"}},
                "fields": "userEnteredFormat.wrapStrategy",
            }
        }
    )

    requests.append(
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row_index,
                    "endRowIndex": end_row_index,
                    "startColumnIndex": status_col_index,
                    "endColumnIndex": status_col_index + 1,
                },
                "cell": {"userEnteredFormat": {"backgroundColor": STATUS_CELL_COLOR}},
                "fields": "userEnteredFormat.backgroundColor",
            }
        }
    )

    return requests


def build_merge_requests(
    sheet_id: int,
    start_row_index: int,
    num_rows: int,
    merge_col_indices: list[int],
) -> list[dict[str, Any]]:
    """Cell merges happen only for multi-item orders (as before)."""
    if num_rows <= 1:
        return []

    end_row_index = start_row_index + num_rows
    return [
        {
            "mergeCells": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row_index,
                    "endRowIndex": end_row_index,
                    "startColumnIndex": col,
                    "endColumnIndex": col + 1,
                },
                "mergeType": "MERGE_ALL",
            }
        }
        for col in merge_col_indices
    ]


class GSheetWriter:
    """Writes order data to Google Sheets"""

    def __init__(self) -> None:
        """The client and the spreadsheet are opened once; worksheets, headers and
        the first free row number are cached for the whole run."""
        self.client = get_gspread_client()
        self.spreadsheet: Spreadsheet = self.client.open_by_key(get_settings().TABLE_ID)
        self._worksheets: dict[str, Worksheet] = {}
        self._headers: dict[str, list[str]] = {}
        self._next_rows: dict[str, int] = {}

    def _get_worksheet(self, title: str) -> Worksheet:
        if title not in self._worksheets:
            self._worksheets[title] = self.spreadsheet.worksheet(title)
        return self._worksheets[title]

    def _get_headers(self, worksheet: Worksheet) -> list[str]:
        if worksheet.title not in self._headers:
            self._headers[worksheet.title] = worksheet.row_values(1)
        return self._headers[worksheet.title]

    def _get_next_row(self, worksheet: Worksheet) -> int:
        """The first free row of the sheet (1-based)."""
        if worksheet.title not in self._next_rows:
            self._next_rows[worksheet.title] = len(worksheet.get_all_values()) + 1
        return self._next_rows[worksheet.title]

    def __sort_by_sheets(
        self,
        extension: str,
        smaller_size: float | str,
        customization_info: str | None = None,
    ) -> Worksheet:
        """Routes the order to a sheet using the size and the file extension"""
        sheet_name = select_sheet_name(extension, smaller_size, customization_info)

        if sheet_name == SHEET_ERROR:
            cprint(
                tr(
                    "---Order file not found on the Drive, so the file extension could not be determined for sheet routing.\n"
                    "The order was added to the ERROR sheet---"
                ),
                "warning",
            )
            return self._get_worksheet(sheet_name)

        worksheet = self._get_worksheet(sheet_name)
        cprint(tr("---Routing to sheet: {sheet}---", sheet=worksheet.title), "success")
        return worksheet

    def append_order(
        self,
        order_items: list[dict[str, None | str | int]],
        extension: str,
        smaller_size: float | str,
        customization_info: str | None = None,
    ) -> str | None:
        """Appends the order to Google Sheets with cell highlighting, the text
        clipping strategy and cell merges.

        Returns the name of the sheet the order was written to (for the UI summary).
        """

        if not order_items:
            cprint(
                tr("||| Order not added: the parser found no items in the HTML |||"),
                "error",
            )
            return None

        worksheet = self.__sort_by_sheets(extension, smaller_size, customization_info)
        headers = self._get_headers(worksheet)

        highlight_cols = [headers.index(col) for col in HIGHLIGHT_COLUMNS]
        status_col = headers.index(COL_STATUS)
        merge_cols = [headers.index(col) for col in MERGE_COLUMNS]

        rows = build_rows(order_items, headers)
        start_row = self._get_next_row(worksheet)
        start_row_index = start_row - 1

        red, green, blue = random.choice(MULTI_ITEM_PALETTE)
        rgb = {"red": red, "green": green, "blue": blue}

        requests = [
            build_insert_rows_request(worksheet.id, start_row_index, len(rows)),
            *build_format_requests(
                sheet_id=worksheet.id,
                start_row_index=start_row_index,
                num_rows=len(rows),
                num_columns=len(headers),
                highlight_col_indices=highlight_cols,
                status_col_index=status_col,
                rgb=rgb,
            ),
        ]
        worksheet.spreadsheet.batch_update({"requests": requests})

        worksheet.update(
            rows,
            f"A{start_row}",
            value_input_option=ValueInputOption.user_entered,
        )

        merge_requests = build_merge_requests(
            sheet_id=worksheet.id,
            start_row_index=start_row_index,
            num_rows=len(rows),
            merge_col_indices=merge_cols,
        )
        if merge_requests:
            worksheet.spreadsheet.batch_update({"requests": merge_requests})

        self._next_rows[worksheet.title] = start_row + len(rows)

        cprint("\n" + tr("<<<Order added to the spreadsheet>>>") + "\n", "success")
        return worksheet.title
