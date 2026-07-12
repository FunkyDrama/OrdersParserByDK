"""Etsy order parser."""

import datetime
import re
from typing import Any


from core.console import cprint
from core.i18n import tr
from core.constants import ERROR_VALUE
from marketplaces.base_parser import BaseParser, OrderItem


class EtsyParser(BaseParser):
    """Parses data from an Etsy order"""

    CHANNEL = "Etsy"

    def parse_order(self) -> list[OrderItem]:
        """Parses the order data"""
        self.order_id = self.__get_order_id()
        shipping_label_link = self._resolve_shipping_label_link()
        date = self._today()
        listing_links = self.__get_listing_links()
        store_title = self.__get_store_title()
        address = self.__get_address()
        items_total = self.__get_items_total()
        shipping_total = self.__get_shipping_total_value()
        shipping_price = self.__get_shipping_price()
        postal_service = self.__get_postal_service()
        tracking_number = self.__get_tracking_number()
        tracking_link = self.__get_tracking_link(postal_service, tracking_number)
        shipping_type = self.__get_shipping_type()
        ship_by_date = self.__ship_by_date()
        gift_details = self.__get_gift_details()
        vat_details = self.__get_vat_information()
        customer_note = self.__get_customer_note()

        files = self._files_or_placeholder(self._search_link_to_file())

        order_items: list[OrderItem] = []
        items = self.soup.select("tr.col-group.pl-xs-0.pt-xs-3.pr-xs-0.pb-xs-3")

        file_index = 0
        for index, item in enumerate(items):
            listing_title = self.__get_listing_title(item)
            self.sku = self.__get_sku(item, listing_title)
            customization = self.__get_customization(item)
            quantity = self.__get_quantity(item)
            self.size = self.__get_size(item)
            listing_url = (
                listing_links[index] if index < len(listing_links) else "File Not Found"
            )
            file_link, file_index = self._allocate_file_link(files, file_index)

            additional_info = "\n".join(
                filter(
                    None,
                    [
                        gift_details,
                        vat_details,
                        customer_note,
                        (
                            shipping_type
                            if not (
                                shipping_type.startswith("Standard")
                                or shipping_type.startswith("Free")
                            )
                            else None
                        ),
                    ],
                )
            )

            order_items.append(
                self._make_row(
                    additional_info=additional_info,
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
                    shipping_total=shipping_total,
                    shipping_price=shipping_price,
                    total=self._safe_total(items_total, shipping_price, shipping_total),
                )
            )

        return order_items

    def get_smaller_size(self) -> float | str:
        """Extracts the smaller side of the product size for sheet routing
        (for Etsy the size comes from the customization, not the file name)."""
        try:
            if self.size is None:
                return ERROR_VALUE
            size = self.size.split("x")
            width = float(size[0].strip())
            height = float(size[1].strip())
            return float(min(width, height))
        except (AttributeError, ValueError):
            cprint(
                tr("||| Could not get the smaller size for sheet routing |||"), "error"
            )
            return ERROR_VALUE

    def __ship_by_date(self) -> str:
        """Extracts the ship-by deadline date"""
        try:
            block = self.soup.find(
                "div",
                class_="flag-img flag-img-right text-right vertical-align-top hide-xs hide-sm",
            )

            if not block:
                block = self.soup.find("div", class_="mt-xs-6 mb-xs-4")

            if not block:
                return self._today()

            block_text = block.get_text(separator=" ", strip=True)

            if "Buyer notification" in block_text:
                date_match = re.search(r"\b\w{3}\s\d{1,2},\s\d{4}\b", block_text)
                if date_match:
                    date_str = date_match.group()
                    date_obj = datetime.datetime.strptime(date_str, "%b %d, %Y")
                    formatted = date_obj.strftime("%d.%m.%Y")
                    cprint(f"- {tr('Ship by')}: {formatted}", "success")
                    return formatted

            if "Ship by" in block_text:
                date_match = re.search(r"Ship by\s(\w{3}\s\d{1,2},\s\d{4})", block_text)
                if date_match:
                    date_str = date_match.group(1)
                    date_obj = datetime.datetime.strptime(date_str, "%b %d, %Y")
                    formatted = date_obj.strftime("%d.%m.%Y")
                    cprint(f"- {tr('Ship by')}: {formatted}", "success")
                    return formatted

            return self._today()
        except AttributeError:
            return self._today()

    def __get_listing_links(self) -> list[str]:
        """Extracts and normalizes all listing links from the order"""
        listing_urls = []
        try:
            listing_url_matches = re.finditer(
                r"(https://www\.etsy\.com/listing/[^?\s]+)", self.order
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

    def __get_store_title(self) -> str:
        """Extracts the shop name"""
        try:
            store_title = (
                self.soup.find(
                    "span", id="order-details-order-info", class_="display-inline-block"
                )
                .find("a", classname="text-gray-darker")
                .text.strip()
            )
            cprint(f"- {tr('Shop name')}: {store_title}", "success")
            return store_title
        except AttributeError:
            cprint(tr("||| Could not get the shop name |||"), "error")
            return ERROR_VALUE

    def __get_order_id(self) -> str:
        """Extracts the order ID"""
        try:
            order_id = (
                self.soup.find(
                    "span", id="order-details-order-info", class_="display-inline-block"
                )
                .find("a", classname="strong")
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
            listing_block = item.find("div", class_="flag-body prose")
            if listing_block:
                listing_title = listing_block.find(
                    "span", {"data-test-id": "unsanitize"}
                ).text.strip()
            else:
                listing_link = item.find("a", href=re.compile(r"/transaction/"))
                listing_title = (
                    listing_link.get("title", "").strip()
                    if listing_link
                    else item.select_one("p.wt-text-title-small--tight").text.strip()
                )
            cprint(f"- {tr('Product title')}: {listing_title}", "success")
            return listing_title
        except AttributeError:
            cprint(tr("||| Could not get the listing title |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_sku(item: Any, listing_title: str) -> str:
        """Extracts the SKU"""
        try:
            sku = (
                item.find("span", class_="mb-xs-1")
                .find("p")
                .find("span", {"data-test-id": "unsanitize"})
                .text.strip()
            )
        except AttributeError:
            cprint(
                tr(
                    "The SKU is not specified on the listing, trying to get it from the product title"
                ),
                "warning",
            )
            sku = listing_title.split(" ")[-1]
            if sku.isdigit():
                sku = listing_title.split(" ")[-2:]
                sku = " ".join(sku)
        cprint(f"- {tr('Item SKU')}: {sku}", "success")
        return sku

    def __get_address(self) -> str:
        """Extracts the customer address"""
        try:
            destination_block = self.soup.find(
                "div",
                attrs={"data-testid": "destination"},
                class_="panel mb-xs-0 mt-xs-2",
            )
            address_div = destination_block.find(
                "div", class_="address break-word fs-mask"
            ).find("p")
            address_parts = {}

            for span in address_div.find_all("span"):
                class_name = span.get("class", [None])[0]
                if class_name == "name":
                    address_parts["name"] = span.text.strip()
                elif class_name == "first-line":
                    address_parts["first_line"] = span.text.strip()
                elif class_name == "city":
                    address_parts["city"] = span.text.strip()
                elif class_name == "state":
                    address_parts["state"] = span.text.strip()
                elif class_name == "zip":
                    address_parts["zip_code"] = span.text.strip()
                elif class_name == "country-name":
                    address_parts["country_name"] = span.text.strip()

            full_address = f"{address_parts.get('name', '')}\n{address_parts.get('first_line', '')}\n"
            full_address += f"{address_parts.get('city', '')}, {address_parts.get('state', '')} {address_parts.get('zip_code', '')}\n"
            full_address += f"{address_parts.get('country_name', '')}"

            cprint(f"- {tr('Customer address')}:\n{full_address}", "success")
            return full_address

        except AttributeError:
            cprint(tr("||| Could not get the customer address |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_customization(item: Any) -> str | None:
        """Extracts and normalizes the customization info from the order"""
        try:
            customization_container = item.find("div", class_="flag-body prose")
            if customization_container:
                customization_items = " \n".join(
                    [li.get_text() for li in customization_container.find_all("li")]
                )
            else:
                customization_items = "\n".join(
                    [
                        " ".join(li.get_text(" ", strip=True).split())
                        for li in item.select("span.mb-xs-1 li")
                    ]
                )
            customization_items = re.sub(r"\s+:", ":", customization_items)
            customization_items = re.sub(
                r"\bNon\s*-\s*Woven\b", "Non-Woven", customization_items, flags=re.I
            )
            cprint(f"- {tr('Customization')}:\n{customization_items}", "success")
            return customization_items
        except AttributeError:
            return ""

    @staticmethod
    def __get_size(item: Any) -> str:
        """Extracts the product size"""
        try:
            customization_container = item.find("div", class_="flag-body prose")
            if customization_container:
                size_text = customization_container.find_all("li")[0].get_text()
            else:
                size_text = " ".join(
                    li.get_text(" ", strip=True)
                    for li in item.select("span.mb-xs-1 li")
                )

            size_pattern = re.findall(r"(\d+\.?\d*)", size_text)

            if size_pattern and len(size_pattern) >= 2:
                width, height = size_pattern[:2]
                size = f"{width}x{height}"
                cprint(f"- {tr('Product size')}: {size} inches", "success")
                return size
            else:
                cprint(
                    tr(
                        "||| Could not recognize the size from the text: {text} |||",
                        text=size_text,
                    ),
                    "warning",
                )
                return ERROR_VALUE

        except AttributeError:
            cprint(tr("||| Could not get the product size |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_quantity(item: Any) -> int | str:
        """Extracts the item quantity in the order"""
        try:
            quantity = item.select_one("td.col-xs-2.pl-xs-0.text-center").text.strip()
            cprint(f"- {tr('Quantity')}: {quantity}", "success")
            return int(quantity)
        except AttributeError:
            cprint(tr("||| Could not get the quantity |||"), "error")
            return ERROR_VALUE

    def __get_shipping_price(self) -> float | str:
        """Shipping price paid by the customer"""
        try:
            shipping_items = self.soup.find_all(
                "li", class_="col-group wt-p-xs-0 wt-mt-xs-1 wt-mb-xs-1"
            )

            for item in shipping_items:
                if "Shipping price" in item.text:
                    price_div = item.find(
                        "div", class_="col-xs-3 text-right wt-pr-xs-0"
                    )
                    shipping_price = price_div.text.strip()
                    shipping_price_value = self._parse_money(shipping_price)
                    cprint(
                        f"- {tr('Shipping price charged')}: {shipping_price_value}",
                        "success",
                    )
                    return shipping_price_value

            cprint(tr("||| Shipping price charged not found |||"), "error")
            return ERROR_VALUE
        except AttributeError:
            cprint(tr("||| Shipping price charged not found |||"), "error")
            return ERROR_VALUE

    def __get_items_total(self) -> float | str:
        """Extracts the items total"""
        try:
            items_total = (
                self.soup.find("li", class_="col-group wt-p-xs-0 wt-mt-xs-1 wt-mb-xs-1")
                .find_next("div", class_="col-xs-3 text-right wt-pr-xs-0")
                .text.strip()
            )
            items_total = self._parse_money(items_total)
            cprint(f"- {tr('Items total')}: {items_total}", "success")
            return items_total
        except (AttributeError, ValueError):
            cprint(tr("||| Could not get the items total |||"), "error")
            return ERROR_VALUE

    def __get_shipping_total_value(self) -> int | float | str:
        """Shipping cost paid by the seller for the shipping label"""
        try:
            shipping_values = self.soup.find_all(
                "div", class_="wt-flex-md-1 text-right"
            )
            total_shipping: float = 0

            for value in shipping_values:
                values = value.find_all("strong", class_="mr-xs-1")
                for total in values:
                    shipping_cost = self._parse_money(total.text)
                    total_shipping += shipping_cost

            cprint(f"- {tr('Shipping paid by us')}: {total_shipping}", "success")
            return total_shipping
        except (AttributeError, ValueError):
            cprint(tr("||| Could not get the shipping amount we paid |||"), "error")
            return ERROR_VALUE

    def __get_postal_service(self) -> str | None | Any:
        """Extracts the carrier name"""
        try:
            postal_service = (
                self.soup.find("div", class_="text-truncate")
                .find_next("div", class_="pl-xs-1 mr-xs-2")
                .find("p", class_="text-truncate")
                .text.split(" ")[0]
            )
            if postal_service == "UPS®":
                postal_service = postal_service.strip("®")
            cprint(f"- {tr('Carrier')}: {postal_service}", "success")
            return postal_service
        except AttributeError:
            try:
                postal_service_div = self.soup.find_all(
                    "div", class_="display-inline-block"
                )
                for el in postal_service_div:
                    paragraphs = el.find_all("p")
                    for p in paragraphs:
                        if "Shipped" in p.text or "Shipping" in p.text:
                            postal_service = p.text.split(" ")[-1]

                            cprint(
                                f"- {tr('Carrier (label bought outside Etsy)')}: "
                                f"{postal_service}",
                                "success",
                            )
                            return postal_service
                cprint(tr("||| Could not get the carrier name |||"), "error")
                return ERROR_VALUE
            except AttributeError:
                cprint(tr("||| Could not get the carrier name |||"), "error")
                return ERROR_VALUE

    def __get_tracking_number(self) -> str:
        """Extracts the tracking number"""
        try:
            tracking_number = (
                self.soup.find("div", class_="col-xs-9 wt-wrap").find("a").text.strip()
            )
            cprint(f"- {tr('Tracking number')}: {tracking_number}", "success")
            return tracking_number
        except AttributeError:
            cprint(tr("||| Could not get the tracking number |||"), "error")
            return ERROR_VALUE

    def __get_tracking_link(
        self, postal_service: str | None, tracking_number: str
    ) -> str | None:
        """Extracts the tracking link"""
        try:
            tracking_link = self._known_tracking_link(postal_service, tracking_number)
            if tracking_link is not None:
                return tracking_link
            return (
                self.soup.find("div", class_="col-xs-9 wt-wrap").find("a").get("href")
            )
        except AttributeError:
            cprint(tr("||| Could not get the tracking link |||"), "error")
            return ERROR_VALUE

    def __get_shipping_type(self) -> str:
        """Extracts the shipping method"""
        try:
            shipping_type = (
                self.soup.find("div", class_="strong text-body-smaller")
                .find("span", {"data-test-id": "unsanitize"})
                .text.strip()
            )
            if shipping_type == "Standard Shipping":
                shipping_type = "Standard"
            cprint(f"- {tr('Shipping method')}: {shipping_type}", "success")
            return shipping_type
        except AttributeError:
            cprint(tr("||| Shipping method not found |||"), "error")
            return ERROR_VALUE

    def __get_gift_details(self) -> str | None:
        """Extracts gift-wrap and gift-card details when present"""
        try:
            gift_details = self.soup.find("h4", class_="mb-xs-2").text.strip()
            if gift_details and gift_details == "Gift details":
                gift_block = self.soup.find("div", class_="col-xs-12 col-md-6 pl-xs-0")
                gift_spans = gift_block.find_all("span", class_="ml-xs-1 text-gray")
                gift_texts = [span.get_text(strip=True) for span in gift_spans]
                gift_info = ""
                for span in gift_texts:
                    gift_info += f"{span}\n"
                return gift_info.strip()
            return None
        except AttributeError:
            return None

    def __get_vat_information(self) -> str | None:
        """Inspects customs information when present"""
        try:
            vat_collected = self.soup.find(
                "span", class_="wt-badge wt-ml-xs-1 wt-badge--notificationPrimary"
            ).text.strip()
            if vat_collected == "VAT Collected":
                vat_block = (
                    self.soup.find("div", class_="panel mb-xs-0 mt-xs-2")
                    .find(
                        "div",
                        class_="wt-panel wt-display-block wt-p-xs-3 text-body-smaller wt-bg-gray",
                    )
                    .find("p")
                )

                if vat_block:
                    vat_text = " ".join(vat_block.stripped_strings)
                    return vat_text
            return None
        except AttributeError:
            return None

    def __get_customer_note(self) -> str | None:
        """Extracts the customer note when present"""
        try:
            customer_info = (
                self.soup.find(
                    "div",
                    class_="order-detail-buyer-note bg-blinding-sandstorm panel pointer"
                    " pointer-top-left text-body-smaller p-xs-2 mt-xs-2 mb-xs-0",
                )
                .find("pre", class_="note")
                .find("span", {"data-test-id": "unsanitize"})
            ).text.strip()
            return f"Buyer's message: {customer_info}"
        except AttributeError:
            return None
