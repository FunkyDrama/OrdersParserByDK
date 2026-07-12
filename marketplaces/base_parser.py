"""Base class of the marketplace parsers."""

import datetime
import re
from abc import ABC, abstractmethod
from typing import Any

from bs4 import BeautifulSoup as Soup

from core.console import cprint
from core.i18n import tr
from core.constants import (
    COL_ADDITIONAL_INFO,
    COL_ADDRESS,
    COL_CHANNEL,
    COL_CUSTOMIZATION,
    COL_DATE,
    COL_FILE_LINK,
    COL_ITEMS_TOTAL,
    COL_LISTING_LINK,
    COL_ORDER_ID,
    COL_POSTAL_SERVICE,
    COL_QUANTITY,
    COL_SHIP_BY,
    COL_SHIPPING_LABEL,
    COL_SHIPPING_PRICE,
    COL_SHIPPING_SPEED,
    COL_SHIPPING_TOTAL,
    COL_SKU,
    COL_STATUS,
    COL_STORE,
    COL_TITLE,
    COL_TOTAL,
    COL_TRACK_ID,
    COL_TRACK_PACKAGE,
    DATE_FORMAT,
    ERROR_VALUE,
    FILE_NOT_FOUND,
    TRACKING_URL_TEMPLATES,
)
from google_api.gdrive_finder import GoogleDriveFinder

OrderItem = dict[str, None | str | int]


class BaseParser(ABC):
    """Shared infrastructure of a single-order parser."""

    CHANNEL: str = ""

    def __init__(self, order: str, finder: GoogleDriveFinder | None = None) -> None:
        """Initializes the order data variables and the Soup instance."""
        self.order = order
        self.soup = Soup(order, "lxml")
        self.finder = finder if finder is not None else GoogleDriveFinder()
        self.sku: str | None = None
        self.order_id: str | None = None
        self.size: str | None = None

    @abstractmethod
    def parse_order(self) -> list[OrderItem]:
        """Parses the order into a list of spreadsheet rows."""

    def _today(self) -> str:
        """Today's date"""
        self.today = datetime.date.today().strftime(DATE_FORMAT)
        cprint(f"- {tr('Processing date')}: {self.today}", "success")
        return self.today

    # ------------------------------------------------------------------
    # Google Drive
    # ------------------------------------------------------------------
    def _search_link_to_file(self) -> list[dict[str, Any]] | None:
        """Searches for the file by order ID, then by SKU."""
        file_link = self.finder.search_file_by_name(
            query=f"name contains '{self.order_id}' and not name contains '.pdf'"
        )
        if file_link is None:
            file_link = self.finder.search_file_by_name(
                query=f"name contains '{self.sku}' and not name contains '.pdf'"
            )
        return file_link

    def _resolve_shipping_label_link(self) -> Any:
        """Uploads the {order_id}.pdf shipping label; if it is not next to the app —
        searches for an already uploaded PDF on Drive."""
        shipping_label_link = self.finder.upload_shipping_labels(self.order_id)  # type: ignore[arg-type]
        if shipping_label_link == FILE_NOT_FOUND:
            file_result = self.finder.search_file_by_name(
                query=f"name contains '{self.order_id}' and name contains '.pdf'"
            )
            shipping_label_link = (
                file_result[0]["link"] if file_result else FILE_NOT_FOUND
            )
        return shipping_label_link

    @staticmethod
    def _files_or_placeholder(
        files: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """An empty search result is replaced with the File Not Found placeholder."""
        if not files:
            return [{"link": FILE_NOT_FOUND, "name": FILE_NOT_FOUND}]
        return files

    @staticmethod
    def _allocate_file_link(
        files: list[dict[str, Any]], file_index: int
    ) -> tuple[str, int]:
        """Hands the next item its file link (the legacy file_index pattern)."""
        if file_index < len(files) and files[file_index]["name"] != FILE_NOT_FOUND:
            return files[file_index]["link"], file_index + 1
        return FILE_NOT_FOUND, file_index

    def get_extension(self) -> str:
        """Extracts the file extension used later for sheet routing"""
        files = self._search_link_to_file()

        if files and isinstance(files, list):
            for file in files:
                if file["name"] != FILE_NOT_FOUND:
                    return file["name"].split(".")[-1]
            return "Unknown"
        return "Unknown"

    def get_smaller_size(self) -> float | str:
        """Extracts the smaller side of the product size for sheet routing."""
        files = self._search_link_to_file()
        try:
            if files and isinstance(files, list):
                for file in files:
                    if file["name"] != FILE_NOT_FOUND:
                        size_from_name = file["name"].split(" ")[0]
                        if "," in size_from_name:
                            size_from_name = size_from_name.replace(",", ".")
                        size = size_from_name.split("x")
                        width = float(size[0].strip())
                        height = float(size[1].strip())
                        return float(min(width, height))
            cprint(
                tr("||| Could not get the smaller size for sheet routing |||"), "error"
            )
            return ERROR_VALUE
        except (ValueError, AttributeError, IndexError):
            cprint(
                tr("||| Could not get the smaller size for sheet routing |||"), "error"
            )
            return ERROR_VALUE

    @staticmethod
    def _known_tracking_link(
        postal_service: str | None, tracking_number: str | None
    ) -> str | None:
        """Tracking link for a known carrier (USPS/UPS/FedEx/DHL); None when the carrier is unknown."""
        template = TRACKING_URL_TEMPLATES.get(postal_service or "")
        if template is None:
            return None
        tracking_link = template.format(number=tracking_number)
        cprint(f"- {tr('Tracking link')}: {tracking_link}", "success")
        return tracking_link

    @staticmethod
    def _safe_total(
        items_total: float | str,
        shipping_price: float | int | str,
        shipping_total: float | int | str,
    ) -> float | str:
        """Total = (items + customer shipping) − our shipping."""
        try:
            return (items_total + shipping_price) - shipping_total  # type: ignore[operator]
        except TypeError:
            cprint(
                tr(
                    "||| Could not compute the Total: some amounts failed to parse, "
                    "the cell will hold !ERROR! — check the order manually |||"
                ),
                "warning",
            )
            return ERROR_VALUE

    @staticmethod
    def _parse_money(value: str) -> float:
        """Converts a money string into a numeric value"""
        cleaned = re.sub(r"[^\d.-]", "", value.replace(",", ""))
        if not re.search(r"\d", cleaned):
            return 0
        return float(cleaned)

    def _make_row(
        self,
        *,
        date: str,
        store_title: str,
        sku: str | None,
        listing_link: str | None,
        listing_title: str,
        address: str | None,
        quantity: int | str,
        customization: str | None,
        file_link: str,
        shipping_label_link: Any,
        tracking_number: str,
        ship_by_date: str,
        postal_service: str | None,
        shipping_type: str,
        tracking_link: str | None,
        items_total: float | str,
        shipping_total: float | int | str,
        shipping_price: float | int | str | None,
        total: float | str,
        additional_info: str | None = None,
        status: None = None,
    ) -> dict[str | Any, str | None | Any]:
        """The single row dict: column keys are defined once for all parsers."""
        return {
            COL_STATUS: status,
            COL_ADDITIONAL_INFO: additional_info,
            COL_DATE: date,
            COL_STORE: store_title,
            COL_CHANNEL: self.CHANNEL,
            COL_SKU: sku,
            COL_LISTING_LINK: listing_link,
            COL_ORDER_ID: self.order_id,
            COL_TITLE: listing_title,
            COL_ADDRESS: address,
            COL_QUANTITY: quantity,
            COL_CUSTOMIZATION: customization,
            COL_FILE_LINK: file_link,
            COL_SHIPPING_LABEL: shipping_label_link,
            COL_TRACK_ID: tracking_number,
            COL_SHIP_BY: ship_by_date,
            COL_POSTAL_SERVICE: postal_service,
            COL_SHIPPING_SPEED: shipping_type,
            COL_TRACK_PACKAGE: tracking_link,
            COL_ITEMS_TOTAL: items_total,
            COL_SHIPPING_TOTAL: shipping_total,
            COL_SHIPPING_PRICE: shipping_price,
            COL_TOTAL: total,
        }
