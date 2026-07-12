"""Amazon order parser module. Extracts order data from Amazon order HTML pages."""

import datetime
from typing import Any


from core.console import cprint
from core.i18n import tr
from core.constants import ERROR_VALUE
from marketplaces.base_parser import BaseParser, OrderItem


class AmazonParser(BaseParser):
    """Parses data from an Amazon order"""

    CHANNEL = "Amazon"

    def parse_order(self) -> list[OrderItem]:
        """Parses the order"""
        self.order_id = self.__get_order_id()
        date = self._today()
        store_title = self.__get_store_title()
        shipping_label_link = self._resolve_shipping_label_link()
        address = self.__get_address()
        items_total = self.__get_items_total()
        shipping_total = self.__get_shipping_total_value()
        shipping_price = self.__get_shipping_price()
        postal_service = self.__get_postal_service()
        tracking_number = self.__get_tracking_number()
        tracking_link = self.__get_tracking_link(postal_service, tracking_number)
        shipping_type = self.__get_shipping_type()
        ship_by_date = self.__ship_by_date()

        files = self._files_or_placeholder(self._search_link_to_file())

        order_items: list[OrderItem] = []
        items = (
            self.soup.find("table", class_="a-keyvalue").find("tbody").find_all("tr")
        )

        file_index = 0
        for item in items:
            listing_title = self.__get_listing_title(item)
            listing_link = self.__get_listing_link(item)
            self.sku = self.__get_sku(listing_title)
            quantity = self.__get_quantity(item)
            customization = self.__get_customization(item)
            file_link, file_index = self._allocate_file_link(files, file_index)

            order_items.append(
                self._make_row(
                    additional_info=(
                        shipping_type
                        if not (
                            shipping_type.startswith("Standard")
                            or shipping_type.startswith("Free")
                        )
                        else None
                    ),
                    date=date,
                    store_title=store_title,
                    sku=self.sku,
                    listing_link=listing_link,
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
                    shipping_total=shipping_total,
                    shipping_price=shipping_price,
                    total=self._safe_total(items_total, shipping_price, shipping_total),
                )
            )

        return order_items

    def __get_store_title(self) -> str:
        """Extracts the shop name"""
        try:
            try:
                store_title = (
                    self.soup.find(
                        "div", class_="dropdown-account-switcher-header-label"
                    )
                    .find(
                        "span", class_="dropdown-account-switcher-header-label-global"
                    )
                    .text.strip()
                )
                cprint(f"- {tr('Shop name')}: {store_title}", "success")
                return store_title
            except AttributeError:
                store_title = (
                    self.soup.find("button", class_="partner-dropdown-button")
                    .find("span")
                    .find("b")
                    .text.strip()
                )
                cprint(f"- {tr('Shop name')}: {store_title}", "success")
                return store_title
        except AttributeError:
            cprint(tr("||| Could not get the shop name |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_sku(listing_title: str) -> str:
        """Extracts the SKU"""
        if "(" in listing_title:
            sku_with_brackets = listing_title.split(" (")[0].strip()
            sku = sku_with_brackets.split(" ")[-1].strip()
        else:
            sku = listing_title.split(" ")[-1].strip()
            if len(sku) == 1:
                sku = listing_title.split(" ")[-2].strip()
        cprint(
            tr(
                "The SKU was taken from the title, verify it after it lands in the spreadsheet!"
            ),
            "warning",
        )
        cprint(f"- {tr('Item SKU')}: {sku}", "success")
        return sku

    @staticmethod
    def __get_listing_link(item: Any) -> str | None:
        """Extracts the listing links"""
        try:
            link = item.find("a", href=True)
            if link:
                listing_link = link.get("href").strip()
                cprint(f"- {tr('Listing link')}: {listing_link}", "success")
                return listing_link
            else:
                cprint(tr("||| Could not find the listing link |||"), "error")
                return None
        except Exception as e:
            cprint(
                tr(
                    "||| Error while searching for the listing link: {error} |||",
                    error=str(e),
                ),
                "error",
            )
            return None

    def __get_order_id(self) -> str:
        """Extracts the order ID"""
        try:
            order_id = (
                self.soup.find("div", class_="a-row a-spacing-mini")
                .find("span", {"data-test-id": "order-id-value"}, class_="a-text-bold")
                .text.strip()
            )
            cprint(f"- {tr('Order ID')}: {order_id}", "success")
            return order_id
        except AttributeError:
            cprint(tr("||| Could not get the order ID |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_listing_title(item: Any) -> str:
        """Extracts the product title"""
        try:
            listing_title = item.find(
                "div", class_="more-info-column-word-wrap-break-word"
            ).text.strip('"')
            cprint(f"- {tr('Product title')}: {listing_title}", "success")
            return listing_title
        except AttributeError:
            cprint(tr("||| Could not get the listing title |||"), "error")
            return ERROR_VALUE

    def __get_address(self) -> str:
        """Generic extraction and multi-line formatting of the customer address"""
        try:
            address_div = self.soup.find(
                "div", {"data-test-id": "shipping-section-buyer-address"}
            )

            phone_number_tag = self.soup.find(
                "span", {"data-test-id": "shipping-section-phone"}
            )
            phone_number = phone_number_tag.text.strip() if phone_number_tag else None

            try:
                address_parts = []

                for part in address_div.children:
                    if isinstance(part, str) and part.strip() == "":
                        continue

                    text = part.get_text(strip=True).replace("\xa0", " ")
                    if text:
                        address_parts.append(text)

                if len(address_parts) == 4:
                    full_address = f"{address_parts[0]}\n{address_parts[1]} {address_parts[2]} {address_parts[3]}"
                elif len(address_parts) == 5:
                    street_address = "\n".join(address_parts[:-2])
                    city_state_zip = f"{address_parts[-2]} {address_parts[-1]}"
                    full_address = f"{street_address} {city_state_zip}"
                elif len(address_parts) > 5:
                    street_address = "\n".join(address_parts[:-3])
                    city_state_zip = (
                        f"{address_parts[-3]} {address_parts[-2]}\n{address_parts[-1]}"
                    )
                    full_address = f"{street_address} {city_state_zip}"
                else:
                    full_address = "\n".join(address_parts)

                if phone_number:
                    full_address += f"\nPhone: {phone_number}"

                cprint(f"- {tr('Customer address')}:\n{full_address}", "success")
                return full_address

            except IndexError:
                cprint(
                    tr("||| The address is too long/short, could not process it |||"),
                    "error",
                )
                return ERROR_VALUE

        except AttributeError:
            cprint(tr("||| Could not get the customer address |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_quantity(item: Any) -> int | str:
        """Extracts the quantity of a specific item"""
        try:
            quantity_td = item.find("td", text=True)
            quantity = quantity_td.text.strip()
            cprint(f"- {tr('Quantity')}: {quantity}", "success")
            return int(quantity)
        except AttributeError:
            cprint(tr("||| Could not get the quantity |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_customization(item: Any) -> str:
        """Extracts the customization info from the order"""
        try:
            customization_block = item.find(
                "div", class_="a-row a-expander-container a-expander-extend-container"
            )
            customization_items = "".join(
                [line.text + "\n" for line in customization_block.find_all("div")][3::]
            ).replace("\xa0", " ")
            cprint(f"- {tr('Customization')}:\n{customization_items}", "success")
            return customization_items.strip()
        except AttributeError:
            cprint(
                tr("||| Could not get the customization, it may not be specified |||"),
                "warning",
            )
            return ""

    def __get_items_total(self) -> float | int:
        """Extracts the items total"""
        try:
            items_total = (
                self.soup.find(
                    "div",
                    class_="a-row a-spacing-none order-details-bordered-box-sale-proceeds",
                )
                .find("td", class_="a-text-right a-align-bottom")
                .find("span", class_="a-color-")
                .text.strip()
            )
            if items_total.startswith("CA"):
                items_total = items_total.replace("CA", "")
            items_total = float(items_total.strip("$"))
            cprint(f"- {tr('Items total')}: {items_total}", "success")
            return items_total
        except AttributeError:
            cprint(tr("||| Could not get the items total |||"), "error")
            return 0

    def __get_shipping_total_value(self) -> float | int:
        """Shipping cost paid by the seller for the shipping label"""
        try:
            shipping_values = self.soup.find(
                "div", class_="a-box-group a-spacing-top-micro"
            ).find("span", class_="a-color-")
            total_shipping = shipping_values.text.strip("$")

            cprint(f"- {tr('Shipping paid by us')}: {total_shipping}", "success")
            return float(total_shipping)
        except (AttributeError, ValueError):
            cprint(tr("||| Could not get the shipping amount we paid |||"), "error")
            return 0

    def __get_shipping_price(self) -> float | int:
        """Shipping price paid by the customer"""
        try:
            order_total = self.soup.find(
                "div",
                class_="a-row a-spacing-none order-details-bordered-box-sale-proceeds",
            )
            if "Shipping total" in order_total.text:
                shipping_total = (
                    order_total.find_all("td")[3]
                    .find("span", class_="a-color-")
                    .text.strip()
                )
                if shipping_total.startswith("CA"):
                    shipping_total = shipping_total.replace("CA", "")
                shipping_price_value = float(shipping_total.strip("$"))
            else:
                shipping_price_value = 0
            cprint(
                f"- {tr('Shipping price charged')}: {shipping_price_value}", "success"
            )
            return shipping_price_value
        except (AttributeError, IndexError):
            cprint(tr("||| Shipping price charged not found |||"), "error")
            return 0

    def __ship_by_date(self) -> str:
        """Extracts the ship-by deadline date"""
        try:
            div = self.soup.find("div", class_="a-box-group a-spacing-top-micro")
            date_div = div.find_all("div", class_="a-column a-span3")[0].text.strip()

            if date_div:
                amazon_date = datetime.datetime.strptime(date_div, "%a, %b %d, %Y")
                parsed_date_str = self._today()
                parsed_date = datetime.datetime.strptime(parsed_date_str, "%d.%m.%Y")

                if amazon_date < parsed_date:
                    amazon_date = parsed_date

                formatted_date = amazon_date.strftime("%d.%m.%Y")

            else:
                formatted_date = self._today()

            cprint(f"- {tr('Ship by')}: {formatted_date}", "success")
            return formatted_date

        except AttributeError:
            formatted_date = self._today()
            cprint(f"- {tr('Ship by')}: {formatted_date}", "success")
            return formatted_date

    def __get_postal_service(self) -> str:
        """Extracts the carrier name"""
        try:
            postal_service_divs = self.soup.find(
                "div", class_="a-box-group a-spacing-top-micro"
            )
            postal_service = postal_service_divs.find_all(
                "div", class_="a-column a-span3"
            )[1].text.strip()
            cprint(f"- {tr('Carrier')}: {postal_service}", "success")
            return postal_service
        except AttributeError:
            cprint(tr("||| Could not get the carrier name |||"), "error")
            return ERROR_VALUE

    def __get_tracking_number(self) -> str:
        """Extracts the tracking number"""
        tracking_number = self.soup.find(
            "a",
            class_="a-popover-trigger a-declarative",
            attrs={"data-test-id": "tracking-id-value"},
        )
        if tracking_number:
            tracking_number = tracking_number.text.strip()
            cprint(f"- {tr('Tracking number')}: {tracking_number}", "success")
            return tracking_number

        tracking_number = self.soup.find(
            "span", attrs={"data-test-id": "tracking-id-value"}
        )
        if tracking_number:
            tracking_number = tracking_number.text.strip()
            cprint(
                f"- {tr('Tracking number (label bought outside Amazon)')}: {tracking_number}",
                "success",
            )
            return tracking_number
        cprint(tr("||| Could not get the tracking number |||"), "error")
        return ERROR_VALUE

    def __get_tracking_link(
        self, postal_service: str, tracking_number: str
    ) -> str | None:
        """Extracts the tracking link"""
        return self._known_tracking_link(postal_service, tracking_number)

    def __get_shipping_type(self) -> str:
        """Extracts the shipping method"""
        try:
            shipping_type = (
                self.soup.find(
                    "span", {"data-test-id": "order-summary-shipping-service-value"}
                )
                .find("span", class_="")
                .text.strip()
            )
            cprint(f"- {tr('Shipping method')}: {shipping_type}", "success")
            return shipping_type
        except AttributeError:
            cprint(tr("||| Shipping method not found |||"), "error")
            return ERROR_VALUE
