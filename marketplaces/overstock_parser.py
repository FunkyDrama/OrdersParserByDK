"""Overstock order parser."""

import datetime
import re
from typing import Any


from core.console import cprint
from core.i18n import tr
from core.constants import ERROR_VALUE
from marketplaces.base_parser import BaseParser, OrderItem


class OverstockParser(BaseParser):
    """Parses data from an Overstock order"""

    CHANNEL = "Overstock"

    def parse_order(self) -> list[OrderItem]:
        """Parses the order"""
        self.order_id = self.__get_order_id()
        date = self._today()
        store_title = self.__get_store_title()
        listing_links = self.__get_listing_links()
        shipping_label_link = self._resolve_shipping_label_link()
        address = self.__get_address()
        items_total = self.__get_items_total()
        postal_service = self.__get_postal_service()
        tracking_number = self.__get_tracking_number()
        tracking_link = self.__get_tracking_link(postal_service, tracking_number)
        shipping_type = self.__get_shipping_type()
        ship_by_date = self.__ship_by_date()

        files = self._files_or_placeholder(self._search_link_to_file())

        order_items: list[OrderItem] = []
        items = self.soup.find("table", class_="table table-hover data-table").find_all(
            "td", id="lineProductCell"
        )

        file_index = 0
        for index, item in enumerate(items):
            listing_title = self.__get_listing_title(item)
            self.sku = self.__get_sku(item)
            size = self.__get_size(item)
            color = self.__get_color(item)
            customization = self.__get_customization(size, color)
            quantity = self.__get_quantity(item)

            listing_url = (
                listing_links[index] if index < len(listing_links) else "File Not Found"
            )
            file_link, file_index = self._allocate_file_link(files, file_index)

            order_items.append(
                self._make_row(
                    date=date,
                    store_title=store_title,
                    sku=self.sku,
                    listing_link=listing_url,
                    listing_title=listing_title,
                    address=address,
                    quantity=quantity,
                    customization=customization,
                    file_link=file_link,
                    shipping_label_link=shipping_label_link,
                    tracking_number=tracking_number,
                    ship_by_date=ship_by_date,
                    postal_service=postal_service,
                    shipping_type=shipping_type,
                    tracking_link=tracking_link,
                    items_total=items_total,
                    shipping_total=0,
                    shipping_price=0,
                    total=items_total,
                )
            )

        return order_items

    def __get_order_id(self) -> str | None | Any:
        """Extracts the order ID"""
        try:
            order_id_div = self.soup.find_all("div", id="soId")
            for el in order_id_div:
                if el.find("h6").text.strip() == "Retailer Order #":
                    order_id = el.find("p").text.strip()
                    cprint(f"- {tr('Order ID')}: {order_id}", "success")
                    return order_id
            return None
        except AttributeError:
            cprint(tr("||| Could not get the order ID |||"), "error")
            return ERROR_VALUE

    def __get_store_title(self) -> str:
        """Extracts the shop name"""
        try:
            store_title = self.soup.find("div", id="soChannel").find("p").text.strip()
            cprint(f"- {tr('Shop name')}: {store_title}", "success")
            return store_title
        except AttributeError:
            cprint(tr("||| Could not get the shop name |||"), "error")
            return ERROR_VALUE

    def __get_address(self) -> str | None:
        """Extracts the customer address"""
        try:
            address_block = self.soup.find("div", id="soShippingAddress").find("p")
            address_parts = [br.get_text(strip=True) for br in address_block]
            address = "\n".join(
                address_parts.strip()
                for address_parts in address_parts
                if address_parts.strip()
            )
            cprint(f"- {tr('Shipping address')}:\n{address}", "success")
            return address
        except AttributeError:
            cprint(tr("||| Could not get the shipping address |||"), "error")
            return ERROR_VALUE

    def __get_items_total(self) -> float | str:
        """Extracts the items total"""
        try:
            items_rows = self.soup.find_all("td", id="lineFirstCostCell")
            items_total: float = 0
            for row in items_rows:
                items_total += float(row.text.strip().replace("$", ""))

            cprint(f"- {tr('Order total')}: {items_total}", "success")
            return items_total
        except AttributeError:
            cprint(tr("||| Could not get the order total |||"), "error")
            return ERROR_VALUE

    def __get_listing_links(self) -> list[str]:
        """Extracts and normalizes all listing links from the order"""
        listing_urls = []
        try:
            listing_url_matches = re.finditer(
                r"(https://www\.(?:overstock|bedbathandbeyond)\.com/[^?\s]+)",
                self.order,
            )
            for match in listing_url_matches:
                listing_url = match.group(1)
                listing_urls.append(listing_url)
                cprint(f"- {tr('Listing link')}: {listing_url}", "success")

            if not listing_urls:
                cprint(tr("||| No listing links found |||"), "error")
                return [ERROR_VALUE]

            return listing_urls
        except Exception as e:
            cprint(
                tr("||| Error while getting the listing links: {error} |||", error=e),
                "error",
            )
            return [ERROR_VALUE]

    @staticmethod
    def __get_listing_title(item: Any) -> str:
        """Extracts the product title"""
        try:
            listing_title = item.find("p", class_="listing-title")
            if listing_title:
                listing_title = listing_title.text.strip()
            cprint(f"- {tr('Product title')}: {listing_title}", "success")
            return listing_title
        except AttributeError:
            cprint(tr("||| Could not get the listing title |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_sku(item: Any) -> str:
        """Extracts the SKU"""
        try:
            sku = item.find("div").text.strip()
            cprint(f"- {tr('Item SKU')}: {sku}", "success")
            return sku
        except AttributeError:
            cprint(tr("||| Could not get the SKU |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_size(item: Any) -> str | None:
        """Extracts the product size"""
        patterns = [
            r"\b(\d+)\s*x\s*(\d+)\b",  # 35x52
            r"\((\d+)\s*x\s*(\d+)\)",  # (9x14)
            r'(\d+)"?\s*[HhWw]\s*X\s*(\d+)"?\s*[HhWw]',  # 17" H X 22" W
            r"(\d+)\s*inches\s*(\d+)\s*inches",  # 22 inches 26 inches
        ]
        for pattern in patterns:
            match = re.search(pattern, item.text.strip(), re.IGNORECASE)
            if match:
                return f"{match.group(1).strip()}x{match.group(2).strip()} inches"
        return None

    @staticmethod
    def __get_color(item: Any) -> str | None:
        """Extracts the color from the part number"""
        try:
            main_text = item.find(text=True, recursive=False).strip()

            if " - " in main_text:
                color = main_text.split(" - ")[1]
                if len(color.split()) < 2:
                    color = " ".join(color.split()[-2:]).title()
                return color.title().strip()
            return None
        except AttributeError:
            return None

    @staticmethod
    def __get_customization(size: str | None, color: str | None) -> str:
        """Extracts the customization info from the order"""
        try:
            customization_list = []

            if size:
                size_customization = f"Size: {size}"
                customization_list.append(size_customization)

            if color:
                color_customization = f"Color: {color.title().strip()}"
                customization_list.append(color_customization)

            customization = "\n".join(customization_list)
            cprint(f"- {tr('Customization')}:\n{customization}", "success")
            return customization

        except AttributeError:
            cprint(
                tr("||| Could not get the customization, it may not be specified |||"),
                "warning",
            )
            return ""
        except ValueError as e:
            cprint(tr("||| Error: {error} |||", error=e), "error")
            return ""

    @staticmethod
    def __get_quantity(item: Any) -> int | str:
        """Extracts the quantity of a specific item"""
        try:
            quantity_cell = item.find_previous_sibling("td", id="lineQuantityCell")
            if quantity_cell:
                quantity = quantity_cell.text.strip()
                cprint(f"- {tr('Quantity')}: {quantity}", "success")
                return int(quantity)
        except AttributeError:
            cprint(tr("||| Could not get the quantity |||"), "error")
        return ERROR_VALUE

    def __get_postal_service(self) -> str:
        """Extracts the carrier name"""
        try:
            postal_service = self.soup.find_all(
                "span", class_="carrierCode existing_carrier"
            )[0].text.strip()
            cprint(f"- {tr('Carrier')}: {postal_service}", "success")
            return postal_service
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the carrier |||"), "error")
            return ERROR_VALUE

    def __get_tracking_number(self) -> str:
        """Extracts the tracking number"""
        try:
            tracking_number = self.soup.find_all(
                "span", class_="existing_tracking_number"
            )[0].text.strip()
            cprint(f"- {tr('Tracking number')}: {tracking_number}", "success")
            return tracking_number
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the tracking number |||"), "error")
            return ERROR_VALUE

    def __get_tracking_link(
        self, postal_service: str, tracking_number: str
    ) -> str | None:
        """Extracts the tracking link"""
        try:
            tracking_link = self._known_tracking_link(postal_service, tracking_number)
            if tracking_link:
                return tracking_link
            tracking_link = (
                self.soup.find_all("div", class_="existingShipments")[0]
                .find("a")
                .get("href")
            )
            return tracking_link
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the tracking link |||"), "error")
            return ERROR_VALUE

    def __get_shipping_type(self) -> str:
        """Extracts the shipping method"""
        try:
            shipping_type = (
                self.soup.find("div", id="soShipMethod").find("p").text.strip()
            )
            cprint(f"- {tr('Shipping method')}: {shipping_type}", "success")
            return shipping_type
        except AttributeError:
            cprint(tr("||| Could not get the shipping method |||"), "error")
            return ERROR_VALUE

    def __ship_by_date(self) -> str:
        """Extracts the ship-by deadline date"""
        try:
            ship_by_date_div = self.soup.find_all("div", class_="existingShipments")[0]
            text = ship_by_date_div.get_text(" ", strip=True)
            match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", text)
            if match:
                ship_by_date = match.group(1)
                formatted_date = datetime.datetime.strptime(
                    ship_by_date, "%m/%d/%Y"
                ).strftime("%d.%m.%Y")
                cprint(f"- {tr('Ship by')}: {formatted_date}", "success")
                return formatted_date
            return self._today()
        except (AttributeError, IndexError):
            formatted_date = self._today()
            cprint(f"- {tr('Ship by')}: {formatted_date}", "success")
            return formatted_date
