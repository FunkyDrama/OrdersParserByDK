"""Wayfair order parser."""

import datetime
import re
from typing import Any


from core.console import cprint
from core.i18n import tr
from core.constants import ERROR_VALUE, WALLPAPER_PATTERN
from marketplaces.base_parser import BaseParser, OrderItem


class WayfairParser(BaseParser):
    """Parses data from a Wayfair order"""

    CHANNEL = "Wayfair"

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
        items = self.soup.find("tbody", attrs={"data-hb-id": "TableBody"}).find_all(
            "tr", attrs={"data-hb-id": "TableRow"}
        )

        file_index = 0
        for index, item in enumerate(items):
            listing_title = self.__get_listing_title(item)
            self.sku = self.__get_sku(item)
            size = self.__get_size()
            color = self.__get_color()
            customization = self.__get_customization(item, size, color)
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

    def __get_order_id(self) -> str:
        """Extracts the order ID"""
        try:
            order_id = self.soup.find(
                "h1",
                class_="b62nt518y mb5j687 mb5j68d mb5j68v",
                attrs={"data-hb-id": "Heading"},
            ).text.strip()
            cprint(f"- {tr('Order ID')}: {order_id}", "success")
            return order_id
        except AttributeError:
            cprint(tr("||| Could not get the order ID |||"), "error")
            return ERROR_VALUE

    def __get_store_title(self) -> str:
        """Extracts the shop name"""
        try:
            store_title = self.soup.find_all(
                "strong", {"data-tag-default": "order-details_orderDetails_strong"}
            )[-1].text.strip()
            cprint(f"- {tr('Shop name')}: {store_title}", "success")
            return store_title
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the shop name |||"), "error")
            return ERROR_VALUE

    def __get_address(self) -> str | None:
        """Extracts the customer address"""
        try:
            address_block = self.soup.find_all(
                "div", attrs={"data-tag-default": "order-details_orderDetails_Text_48"}
            )[0]
            if address_block:
                address = "\n".join(address_block.stripped_strings)
                cprint(f"- {tr('Shipping address')}:\n{address}", "success")
                return address
            return None
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the shipping address |||"), "error")
            return ERROR_VALUE

    def __get_items_total(self) -> float | str:
        """Extracts the items total"""
        try:
            items_total = self.soup.find_all(
                "strong", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )[4].text.strip()
            items_total = float(items_total.strip("$").replace(",", ""))
            cprint(f"- {tr('Order total')}: {items_total}", "success")
            return items_total
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the order total |||"), "error")
            return ERROR_VALUE

    def __get_postal_service(self) -> str:
        """Extracts the carrier name"""
        try:
            postal_service = self.soup.find_all(
                "strong", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )[6].text.strip()
            if postal_service == "Order Not Processed On Time":
                postal_service = self.soup.find_all(
                    "strong",
                    attrs={"data-tag-default": "order-details_orderDetails_Text"},
                )[8].text.strip()
            if postal_service == "US Mail":
                postal_service = "USPS"
            if postal_service == "United Parcel Service":
                postal_service = "UPS"
            cprint(f"- {tr('Carrier')}: {postal_service}", "success")
            return postal_service
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the carrier |||"), "error")
            return ERROR_VALUE

    def __get_tracking_number(self) -> str:
        """Extracts the tracking number"""
        try:
            fields = self.soup.find_all(
                "p", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )
            tracking_number = None
            for index, field in enumerate(fields):
                if field.text.strip() != "Tracking Number(s)":
                    continue
                if index + 1 < len(fields):
                    candidate = fields[index + 1].text.strip()
                    if self.__is_tracking_number(candidate):
                        tracking_number = candidate
                break

            if not tracking_number:
                raise AttributeError

            if ", " in tracking_number:
                tracking_number = tracking_number.split(", ")
                tracking_number = "\n".join(tracking_number)
            cprint(f"- {tr('Tracking number')}: {tracking_number}", "success")
            return tracking_number
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the tracking number |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __is_tracking_number(value: str) -> bool:
        """Tells a real tracking number apart from neighboring labels such as Delivery Date."""
        if not value:
            return False
        if value in {"Tracking Number(s)", "Delivery Date"}:
            return False
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", value):
            return False
        return bool(re.search(r"\d", value)) and bool(
            re.search(r"[A-Za-z0-9]{6,}", value)
        )

    def __get_tracking_link(self, postal_service: str, tracking_number: str) -> str:
        """Extracts tracking links (there may be several tracking numbers)"""
        try:
            if tracking_number == ERROR_VALUE:
                raise AttributeError

            tracking_numbers = (
                tracking_number.split("\n")
                if "\n" in tracking_number
                else [tracking_number]
            )
            tracking_links: dict[str, None] = {}
            for number in tracking_numbers:
                tracking_link = self._known_tracking_link(postal_service, number)
                if tracking_link:
                    tracking_links[tracking_link] = None

            if not tracking_links:
                cprint(tr("||| Could not get the tracking link |||"), "error")
                return ERROR_VALUE

            return "\n\n".join(tracking_links)
        except AttributeError:
            cprint(tr("||| Could not get the tracking link |||"), "error")
            return ERROR_VALUE

    def __get_shipping_type(self) -> str:
        """Extracts the shipping method"""
        try:
            shipping_type = self.soup.find_all(
                "strong", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )[8].text.strip()
            if shipping_type.startswith("FedEx"):
                shipping_type = shipping_type.replace("FedEx", "").strip()
            cprint(f"- {tr('Shipping method')}: {shipping_type}", "success")
            return shipping_type
        except (AttributeError, IndexError):
            cprint(tr("||| Could not get the shipping method |||"), "error")
            return ERROR_VALUE

    def __ship_by_date(self) -> str:
        """Extracts the ship-by deadline date"""
        try:
            ship_by_date = self.soup.find_all(
                "strong", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )[1].text.strip()
            formatted_date = datetime.datetime.strptime(
                ship_by_date, "%m/%d/%Y"
            ).strftime("%d.%m.%Y")
            cprint(f"- {tr('Ship by')}: {formatted_date}", "success")
            return formatted_date
        except (AttributeError, IndexError):
            formatted_date = self._today()
            cprint(f"- {tr('Ship by')}: {formatted_date}", "success")
            return formatted_date

    def __get_listing_links(self) -> list[str]:
        """Extracts and normalizes all listing links from the order"""
        listing_urls = []
        try:
            listing_url_matches = re.finditer(
                r"(https://www\.wayfair\.com/[^?\s]+)", self.order
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
            titles = item.find_all(
                "p",
                attrs={
                    "data-tag-default": "order-details_useOrderItemsTableColumns_Text",
                    "data-hb-id": "Text",
                },
            )
            listing_titles = [
                title.text.strip()
                for title in titles
                if title.find_parent("div", class_="b62nt5ct")
            ]
            listing_title = "".join(listing_titles)
            cprint(f"- {tr('Product title')}: {listing_title}", "success")
            return listing_title
        except AttributeError:
            cprint(tr("||| Could not get the listing title |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_sku(item: Any) -> str:
        """Extracts the SKU"""
        try:
            sku_div = item.find_all("p", class_="b62nt5bl b62nt518y")
            skus = [
                sku.text.strip()
                for sku in sku_div
                if sku.find_parent(
                    "div", class_="b62nt513e b62nt5hp b62nt59r b62nt51bd"
                )
            ]
            sku = "".join(skus)
            cprint(f"- {tr('Item SKU')}: {sku}", "success")
            return sku
        except AttributeError:
            cprint(tr("||| Could not get the SKU |||"), "error")
            return ERROR_VALUE

    def __get_customization(
        self, item: Any, size: str | None, color: str | None
    ) -> str:
        """Extracts the customization info from the order"""
        try:
            customization_list = []

            material = self.__get_material_from_sku()
            if material:
                customization_list.append(f"Material: {material}")

            if size:
                size_customization = f"Size: {size}"
                customization_list.append(size_customization)

            if color:
                color_customization = f"Color: {color.title().strip()}"
                customization_list.append(color_customization)

            headers = self.soup.find("thead").find_all("th")
            customization_index = None
            for idx, header in enumerate(headers):
                if header.text.strip() == "Customization Text":
                    customization_index = idx
                    break

            if customization_index is None:
                customization_index = 0

            cells = item.find_all("td")
            if len(cells) > customization_index:
                customization_text = cells[customization_index].get_text(strip=True)
                if customization_text:
                    customization_list.append(f"Personalization: {customization_text}")

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

    def __get_material_from_sku(self) -> str | None:
        """Wallpaper material (Peel and Stick / Non-Woven) from the SKU"""
        if not self.sku:
            return None

        match = WALLPAPER_PATTERN.search(self.sku)
        if not match:
            return None

        material = match.group(0).lower()

        if "peel" in material:
            return "Peel and Stick"
        if "woven" in material:
            return "Non-Woven"

        return None

    def __get_color(self) -> str | None:
        """Extracts the color from the part number"""
        try:
            if not self.sku:
                return None

            sku = self.sku.lower()

            size_match = re.search(r"\d+\s*x\s*\d+", sku)
            if not size_match:
                return None

            after_size = sku[size_match.end() :].strip()

            if not after_size:
                return None

            after_size = WALLPAPER_PATTERN.sub("", after_size).strip()

            after_size = re.sub(r"[^a-z\s]", "", after_size).strip()

            if not after_size:
                return None

            parts = after_size.split()

            if len(parts) >= 2:
                return f"{parts[0]} {parts[1]}".title()
            else:
                return parts[0].title()

        except Exception:
            return None

    def __get_size(self) -> str | None:
        """Extracts the product size from the SKU"""
        patterns = [
            r"\b(\d+)\s*x\s*(\d+)\b",  # 35x52
            r"\((\d+)\s*x\s*(\d+)\)",  # (9x14)
            r'(\d+)"?\s*[HhWw]\s*X\s*(\d+)"?\s*[HhWw]',  # 17" H X 22" W
        ]
        if self.sku is None:
            return None
        for pattern in patterns:
            match = re.search(pattern, self.sku, re.IGNORECASE)
            if match:
                return f"{match.group(1).strip()}x{match.group(2).strip()} inches"
        return None

    @staticmethod
    def __get_quantity(item: Any) -> int | str:
        """Extracts the quantity of a specific item"""
        try:
            quantity_div = item.find_all(
                "p",
                attrs={
                    "data-tag-default": "order-details_useOrderItemsTableColumns_Text",
                    "data-hb-id": "Text",
                },
            )
            quantities = [
                quantity.text.strip()
                for quantity in quantity_div
                if quantity.find_parent(
                    "td",
                    class_="b62nt5ix b62nt5l b62nt51bx b62nt5196 b62nt512h b62nt51d7 _9pl4ko0",
                )
            ]
            quantity = "".join(quantities[2])
            cprint(f"- {tr('Quantity')}: {quantity}", "success")
            return int(quantity)
        except AttributeError:
            cprint(tr("||| Could not get the quantity |||"), "error")
            return ERROR_VALUE
