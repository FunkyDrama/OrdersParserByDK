"""eBay order parser."""

from typing import Any


from core.console import cprint
from core.i18n import tr
from core.constants import ERROR_VALUE
from marketplaces.base_parser import BaseParser, OrderItem


class EbayParser(BaseParser):
    """Parses data from an eBay order"""

    CHANNEL = "Ebay"

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
        total = self.__get_total()
        tracking_number = self.__get_tracking_number()
        postal_service = self.__get_postal_service(tracking_number)
        tracking_link = self.__get_tracking_link(postal_service, tracking_number)
        shipping_type = self.__get_shipping_type()
        ship_by_date = self.__ship_by_date()

        files = self._files_or_placeholder(self._search_link_to_file())

        order_items: list[OrderItem] = []
        items = self.soup.find("div", class_="item-info").find_all(
            "div", class_="lineItemCardInfo__summary"
        )

        file_index = 0
        for item in items:
            listing_title = self.__get_listing_title(item)
            listing_link = self.__get_listing_link(item)
            self.sku = self.__get_sku(item, listing_title)
            quantity = self.__get_quantity(item)
            customization = self.__get_customization(item)
            file_link, file_index = self._allocate_file_link(files, file_index)

            order_items.append(
                self._make_row(
                    additional_info=(
                        shipping_type
                        if not (shipping_type.startswith("Standard"))
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
                    total=total,
                )
            )

        return order_items

    def __get_order_id(self) -> str:
        """Extracts the order ID"""
        try:
            order_id = (
                self.soup.find("div", class_="order-info")
                .find("dd", class_="info-value")
                .text.strip()
            )
            cprint(f"- {tr('Order ID')}: {order_id}", "success")
            return order_id
        except AttributeError:
            cprint(tr("||| Could not get the order ID |||"), "error")
            return ERROR_VALUE

    def __get_store_title(self) -> str:
        """Extracts the shop name"""
        try:
            store_title = "stickalz"
            cprint(f"- {tr('Shop name')}: {store_title}", "success")
            return store_title
        except AttributeError:
            cprint(tr("||| Could not get the shop name |||"), "error")
            return ERROR_VALUE

    def __get_address(self) -> str:
        """Generic extraction and multi-line formatting of the customer address"""
        try:
            address_div = self.soup.find("div", class_="shipping-address").find_all(
                "button", class_="tooltip__host clickable"
            )
            phone_number_tag = self.soup.find("span", id="nid-mu6-3").find("button")
            phone_number = phone_number_tag.text.strip() if phone_number_tag else None

            try:
                address_parts = []

                for part in address_div:
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

    def __get_items_total(self) -> float | int:
        """Extracts the items total"""
        try:
            items_total = (
                self.soup.find("div", class_="earnings")
                .find("dd", class_="amount")
                .find("span", class_="sh-bold")
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
            shipping_values = self.soup.find("div", class_="earnings").find_all(
                "div", class_="data-item"
            )[-1]

            total_shipping: str = "0"
            if "Shipping label" in shipping_values.text.strip():
                total_shipping = shipping_values.find(
                    "span", class_="sh-secondary"
                ).text.strip()
            total_shipping = total_shipping.replace("-", "").replace("$", "")
            if total_shipping.startswith("CA"):
                total_shipping = total_shipping.replace("CA", "")

            cprint(f"- {tr('Shipping paid by us')}: {total_shipping}", "success")
            return float(total_shipping)
        except (AttributeError, ValueError):
            cprint(tr("||| Could not get the shipping amount we paid |||"), "error")
            return 0

    def __get_shipping_price(self) -> float | int:
        """Shipping price paid by the customer"""
        try:
            order_total = self.soup.find("div", class_="buyer-paid").find_all(
                "div", class_="data-item"
            )[1]
            if "Shipping" in order_total.text:
                shipping_total = order_total.find("div", class_="value").text.strip()
                shipping_total = shipping_total.replace("-", "")
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

    def __get_total(self) -> float | int:
        """Order revenue"""
        try:
            order_earnings = (
                self.soup.find_all("dl", class_="total")[-1]
                .find("dd", class_="amount")
                .text.strip()
            )
            order_earnings = float(order_earnings.replace("CA", "").replace("$", ""))

            cprint(f"- {tr('Total')}: {order_earnings}", "success")
            return order_earnings
        except (AttributeError, IndexError):
            cprint(tr("||| Total not found |||"), "error")
            return 0

    def __get_tracking_number(self) -> str:
        """Extracts the tracking number"""
        try:
            tracking_button = (
                self.soup.find("div", class_="shipping-info")
                .find("div", class_="tracking-info")
                .find("button", class_="fake-link")
            )
            if tracking_button:
                tracking_number = tracking_button.text.strip()
            else:
                tracking_div = (
                    self.soup.find("div", class_="shipping-info")
                    .find("div", class_="tracking-info")
                    .find("div", class_="value")
                )
                if tracking_div:
                    tracking_number = tracking_div.text.strip()
                else:
                    tracking_number = None

            if tracking_number:
                cprint(f"- {tr('Tracking number')}: {tracking_number}", "success")
                return tracking_number
            else:
                cprint(tr("||| Could not get the tracking number |||"), "error")
                return ERROR_VALUE

        except AttributeError:
            cprint(tr("||| Could not get the tracking number |||"), "error")
            return ERROR_VALUE

    def __get_postal_service(self, tracking_number: str) -> str | None:
        """Extracts the carrier name from the tracking-number prefix"""
        try:
            postal_service = None
            if tracking_number.startswith("1Z"):
                postal_service = "UPS"
            elif (
                tracking_number.startswith("92")
                or tracking_number.startswith("94")
                or tracking_number.startswith("93")
            ):
                postal_service = "USPS"
            elif tracking_number.startswith("2") or tracking_number.startswith("6"):
                postal_service = "FedEx"
            elif (
                tracking_number.startswith("15")
                or tracking_number.startswith("99")
                or tracking_number.startswith("74")
            ):
                postal_service = "DHL"

            cprint(f"- {tr('Carrier')}: {postal_service}", "success")
            return postal_service
        except AttributeError:
            cprint(tr("||| Could not get the carrier name |||"), "error")
            return ERROR_VALUE

    def __get_tracking_link(
        self, postal_service: str | None, tracking_number: str
    ) -> str | None:
        """Extracts the tracking link"""
        return self._known_tracking_link(postal_service, tracking_number)

    def __get_shipping_type(self) -> str:
        """Extracts the shipping method"""
        try:
            shipping_info_block = (
                self.soup.find("dl", class_="ship-itm")
                .find("dd", class_="info-value")
                .text.strip()
            )
            if "Priority" in shipping_info_block:
                shipping_type = "Expedited"
            elif (
                "2nd Day" in shipping_info_block or "Second Day" in shipping_info_block
            ):
                shipping_type = "Second Day"
            elif "Next Day" in shipping_info_block or "Express" in shipping_info_block:
                shipping_type = "Next Day"
            else:
                shipping_type = "Standard"
            cprint(f"- {tr('Shipping method')}: {shipping_type}", "success")
            return shipping_type
        except AttributeError:
            cprint(tr("||| Shipping method not found |||"), "error")
            return ERROR_VALUE

    def __ship_by_date(self) -> str:
        """Extracts the ship-by deadline date"""
        try:
            formatted_date = self._today()
            cprint(f"- {tr('Ship by')}: {formatted_date}", "success")
            return formatted_date
        except AttributeError:
            formatted_date = self._today()
            cprint(f"- {tr('Ship by')}: {formatted_date}", "success")
            return formatted_date

    @staticmethod
    def __get_listing_title(item: Any) -> str:
        """Extracts the product title"""
        try:
            listing_title = item.find("span", class_="PSEUDOLINK").text.strip()
            cprint(f"- {tr('Product title')}: {listing_title}", "success")
            return listing_title
        except AttributeError:
            cprint(tr("||| Could not get the listing title |||"), "error")
            return ERROR_VALUE

    @staticmethod
    def __get_listing_link(item: Any) -> str:
        """Extracts the listing links"""
        try:
            link = item.find("div", class_="details").find("a", href=True)
            if link:
                listing_link = link.get("href").strip()
                cprint(f"- {tr('Listing link')}: {listing_link}", "success")
                return listing_link
            else:
                cprint(tr("||| Could not find the listing link |||"), "error")
                return ERROR_VALUE
        except Exception as e:
            cprint(
                tr(
                    "||| Error while searching for the listing link: {error} |||",
                    error=str(e),
                ),
                "error",
            )
            return ERROR_VALUE

    @staticmethod
    def __get_sku(item: Any, listing_title: str) -> str | None:
        """Extracts the SKU"""
        try:
            item_block = item.find("div", class_="data-items").find_all(
                "div", class_="info-item"
            )
            for el in item_block:
                if (
                    "MPN" in el.text.strip()
                    or "Manufacturer Part Number" in el.text.strip()
                ):
                    sku = el.find("dd", class_="info-value").text.strip()
                    cprint(f"- {tr('Item SKU')}: {sku}", "success")
                    return sku
        except AttributeError:
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
        return None

    @staticmethod
    def __get_quantity(item: Any) -> int | str:
        """Extracts the quantity of a specific item"""
        try:
            quantity = (
                item.find("div", class_="quantity__value")
                .find("span", class_="sh-bold")
                .text.strip()
            )
            cprint(f"- {tr('Quantity')}: {quantity}", "success")
            return int(quantity)
        except AttributeError:
            cprint(tr("||| Could not get the quantity |||"), "error")
            return ERROR_VALUE

    def __get_customization(self, item: Any) -> str | None:
        """Extracts the customization info from the order"""
        try:
            customization_list = []

            size_block = item.find("div", class_="lineItemCardInfo__aspects spaceTop")
            if size_block:
                size_elements = size_block.find_all("span", class_="sh-bold")
                if len(size_elements) > 1:
                    size_customization = f"Size: {size_elements[1].text.strip()}"
                    customization_list.append(size_customization)

            customization_block = self.soup.find("div", class_="note buyer")
            if customization_block:
                note_content = customization_block.find("div", class_="note-content")
                if note_content:
                    customization_text = note_content.text.strip()
                    customization_list.append(customization_text)

            customization = (
                "\n".join(customization_list) if customization_list else None
            )

            cprint(f"- {tr('Customization')}:\n{customization}", "success")
            return customization
        except Exception as e:
            cprint(
                tr("||| Error while getting the customization: {error} |||", error=e),
                "warning",
            )
            return None
