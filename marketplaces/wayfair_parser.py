import datetime
import re
from typing import Any
from bs4 import BeautifulSoup as Soup
from colorama import Fore, Back

from google_api.gdrive_finder import GoogleDriveFinder
from google_api.gsheet_writer import WALLPAPER_PATTERN


class WayfairParser:
    def __init__(self, order: Any) -> None:
        self.order = order
        self.soup = Soup(order, "lxml")
        self.finder = GoogleDriveFinder()
        self.order_id = None
        self.sku = None

    def parse_order(self) -> list[dict[str, None | str | int]]:
        """Метод парсинга заказа"""
        self.order_id = self.__get_order_id()
        date = self.__get_parse_date(self)
        store_title = self.__get_store_title()
        listing_links = self.__get_listing_links()
        shipping_label_link = self.finder.upload_shipping_labels(self.order_id)
        address = self.__get_address()
        items_total = self.__get_items_total()
        postal_service = self.__get_postal_service()
        tracking_number = self.__get_tracking_number()
        tracking_link = self.__get_tracking_link(postal_service, tracking_number)
        shipping_type = self.__get_shipping_type()
        ship_by_date = self.__ship_by_date()

        files = self.__search_link_to_file()
        if not files:
            files = [{"link": "File Not Found", "name": "File Not Found"}]
        if shipping_label_link == "File Not Found":
            file_result = self.finder.search_file_by_name(
                query=f"name contains '{self.order_id}' and name contains '.pdf'"
            )
            shipping_label_link = (
                file_result[0]["link"] if file_result else "File Not Found"
            )

        order_items = []
        items = self.soup.find("tbody", attrs={"data-hb-id": "TableBody"}).find_all(
            "tr", attrs={"data-hb-id": "TableRow"}
        )

        file_index = 0
        for item in items:
            listing_title = self.__get_listing_title(item)
            self.sku = self.__get_sku(item)
            size = self.__get_size()
            color = self.__get_color()
            customization = self.__get_customization(item, size, color)
            quantity = self.__get_quantity(item)

            listing_url = (
                listing_links[items.index(item)]
                if items.index(item) < len(listing_links)
                else "File Not Found"
            )

            if (
                file_index < len(files)
                and files[file_index]["name"] != "File Not Found"
            ):
                file_link = files[file_index]["link"]
                file_index += 1
            else:
                file_link = "File Not Found"

            order_data = {
                "Status": None,
                "Additional Info": None,
                "Date": date,
                "Store": store_title,
                "Channel": "Wayfair",
                "ASIN/SKU": self.sku,
                "Listing Link": listing_url,
                "Order ID": self.order_id,
                "Title": listing_title,
                "Address/Ship to": address,
                "Quantity": quantity,
                "Customization info": customization,
                "File Link": file_link,
                "Shipping label link": shipping_label_link,
                "Track ID": tracking_number,
                "Ship By": ship_by_date,
                "Postal Service": postal_service,
                "Shipping speed": shipping_type,
                "Track package": tracking_link,
                "Items total": items_total,
                "Shipping total": 0,
                "Shipping price": 0,
                "Total": items_total,
            }
            order_items.append(order_data)

        return order_items

    @staticmethod
    def __get_parse_date(self) -> str:
        """Метод получения сегодняшней даты"""
        self.today = datetime.date.today().strftime("%d.%m.%Y")
        print(
            Fore.GREEN
            + f"- Дата обработки заказа: {Fore.MAGENTA}{self.today}{Back.WHITE}"
            + Back.WHITE
        )
        return self.today

    def __get_order_id(self) -> str:
        """Извлечение номера заказа"""
        try:
            order_id = self.soup.find(
                "h1",
                class_="b62nt518y mb5j687 mb5j68d mb5j68v",
                attrs={"data-hb-id": "Heading"},
            ).text.strip()
            print(
                Fore.GREEN
                + f"- Номер заказа: {Fore.MAGENTA}{order_id}{Back.WHITE}"
                + Back.WHITE
            )
            return order_id
        except AttributeError:
            print(Fore.RED + "||| Не смог получить номер заказа |||" + Back.WHITE)
            return "!ERROR!"

    def __get_store_title(self):
        """Извлечение названия магазина"""
        try:
            store_title = self.soup.find_all(
                "strong", {"data-tag-default": "order-details_orderDetails_strong"}
            )[-1].text.strip()
            print(
                Fore.GREEN
                + f"- Название магазина: {Fore.MAGENTA}{store_title}{Back.WHITE}"
                + Back.WHITE
            )
            return store_title
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Не смог получить название магазина |||" + Back.WHITE)
            return "!ERROR!"

    def __get_address(self) -> str | None:
        """Извлечение адреса"""
        try:
            address_block = self.soup.find_all(
                "div", attrs={"data-tag-default": "order-details_orderDetails_Text_46"}
            )[0]
            if address_block:
                address = "\n".join(address_block.stripped_strings)
                print(
                    Fore.GREEN
                    + f"- Адрес доставки:\n{Fore.MAGENTA}{address}{Back.WHITE}"
                    + Back.WHITE
                )
                return address
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Не смог получить адрес доставки |||" + Back.WHITE)
            return "!ERROR!"

    def __get_items_total(self) -> float | str:
        """Получение общей стоимости товара"""
        try:
            items_total = self.soup.find_all(
                "strong", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )[4].text.strip()
            items_total = float(items_total.strip("$").replace(",", ""))
            print(
                Fore.GREEN
                + f"- Сумма заказа: {Fore.MAGENTA}{items_total}{Back.WHITE}"
                + Back.WHITE
            )
            return items_total
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Не смог получить сумму заказа |||" + Back.WHITE)
            return "!ERROR!"

    def __get_postal_service(self) -> str:
        """Извлечение названия почтовой службы"""
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
            print(
                Fore.GREEN
                + f"- Служба доставки: {Fore.MAGENTA}{postal_service}{Back.WHITE}"
                + Back.WHITE
            )
            return postal_service
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Не смог получить службу доставки |||" + Back.WHITE)
            return "!ERROR!"

    def __get_tracking_number(self) -> str:
        """Извлечение трек-номера"""
        try:
            tracking_number = self.soup.find_all(
                "p", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )[-1].text.strip()
            if tracking_number == "Tracking Number(s)":
                raise AttributeError(
                    Fore.RED + "||| Не смог получить трек-номер |||" + Back.WHITE
                )
            if ", " in tracking_number:
                tracking_number = tracking_number.split(", ")
                tracking_number = "\n".join(tracking_number)
            print(
                Fore.GREEN
                + f"- Трек-номер: {Fore.MAGENTA}{tracking_number}{Back.WHITE}"
                + Back.WHITE
            )
            return tracking_number
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Не смог получить трек-номер |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_tracking_link(postal_service, tracking_number) -> str:
        """Извлечение ссылки на отслеживание посылки"""
        try:
            tracking_numbers = (
                tracking_number.split("\n")
                if "\n" in tracking_number
                else [tracking_number]
            )
            tracking_links = set()
            for number in tracking_numbers:
                tracking_link = None
                if postal_service == "USPS":
                    tracking_link = f"https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1={number}"
                    tracking_links.add(tracking_link)
                elif postal_service == "UPS" or postal_service == "UPS®":
                    tracking_link = f"https://www.ups.com/track?TypeOfInquiryNumber=T&InquiryNumber1={number}&loc=en_US&requester=ST/trackdetails"
                    tracking_links.add(tracking_link)
                elif postal_service == "FedEx":
                    tracking_link = (
                        f"https://www.fedex.com/apps/fedextrack/?tracknumbers={number}"
                    )
                    tracking_links.add(tracking_link)
                elif postal_service == "DHL":
                    tracking_link = f"https://www.dhl.com/us-en/home/tracking/tracking-express.html?submit=1&tracking-id={number}"
                print(
                    Fore.GREEN
                    + f"- Ссылка на отслеживание: {Fore.MAGENTA}{tracking_link}{Back.WHITE}"
                    + Back.WHITE
                )
                tracking_links.add(tracking_link)
            links = "\n\n".join(tracking_links)
            return links
        except AttributeError:
            print(
                Fore.RED
                + "||| Не смог получить ссылку на отслеживание |||"
                + Back.WHITE
            )
            return "!ERROR!"

    def __get_shipping_type(self) -> str:
        """Извлечение типа доставки"""
        try:
            shipping_type = self.soup.find_all(
                "strong", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )[8].text.strip()
            if shipping_type.startswith("FedEx"):
                shipping_type = shipping_type.replace("FedEx", "").strip()
            print(
                Fore.GREEN
                + f"- Тип доставки: {Fore.MAGENTA}{shipping_type}{Back.WHITE}"
                + Back.WHITE
            )
            return shipping_type
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Не смог получить тип доставки |||" + Back.WHITE)
            return "!ERROR!"

    def __ship_by_date(self) -> str:
        """Извлечение крайней даты отправки посылки"""
        try:
            ship_by_date = self.soup.find_all(
                "strong", attrs={"data-tag-default": "order-details_orderDetails_Text"}
            )[1].text.strip()
            formatted_date = datetime.datetime.strptime(
                ship_by_date, "%m/%d/%Y"
            ).strftime("%d.%m.%Y")
            print(
                Fore.GREEN
                + f"- Заказ отправить до: {Fore.MAGENTA}{formatted_date}{Back.WHITE}"
                + Back.WHITE
            )
            return formatted_date
        except (AttributeError, IndexError):
            formatted_date = self.__get_parse_date(self)
            print(
                Fore.GREEN
                + f"- Заказ отправить до: {Fore.MAGENTA}{formatted_date}{Back.WHITE}"
                + Back.WHITE
            )
            return formatted_date

    def __get_listing_links(self) -> list[str]:
        """Извлечение и преобразование всех ссылок на листинги из заказа"""
        listing_urls = []
        try:
            listing_url_matches = re.finditer(
                r"(https://www\.wayfair\.com/[^?\s]+)", self.order
            )
            for match in listing_url_matches:
                listing_url = match.group(1)
                listing_urls.append(listing_url)
                print(
                    Fore.GREEN
                    + f"- Ссылка на листинг: {Fore.MAGENTA}{listing_url}{Back.WHITE}"
                    + Back.WHITE
                )

            if not listing_urls:
                print(
                    Fore.RED
                    + "||| Не найдено ни одной ссылки на листинг |||"
                    + Back.WHITE
                )
                return ["!ERROR!"]

            return listing_urls
        except Exception as e:
            print(
                Fore.RED
                + f"||| Ошибка при получении ссылок на листинги: {e} |||"
                + Back.WHITE
            )
            return ["!ERROR!"]

    def __search_link_to_file(self) -> list[dict[str, Any]] | None:
        """Метод поиска ссылки на файл по номеру заказа или SKU"""
        file_link = self.finder.search_file_by_name(
            query=f"name contains '{self.order_id}' and not name contains '.pdf'"
        )
        if file_link is None:
            file_link = self.finder.search_file_by_name(
                query=f"name contains '{self.sku}' and not name contains '.pdf'"
            )
        return file_link

    @staticmethod
    def __get_listing_title(item) -> str:
        """Извлечение названия товара"""
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
            listing_titles = "".join(listing_titles)
            print(
                Fore.GREEN
                + f"- Название товара: {Fore.MAGENTA}{listing_titles}{Back.WHITE}"
                + Back.WHITE
            )
            return listing_titles
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название листинга |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_sku(item) -> str:
        """Извлечение SKU"""
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
            print(
                Fore.GREEN
                + f"- SKU товара: {Fore.MAGENTA}{sku}{Back.WHITE}"
                + Back.WHITE
            )
            return sku
        except AttributeError:
            print(Fore.RED + "||| Не смог получить SKU |||" + Back.WHITE)
            return "!ERROR!"

    def __get_customization(self, item, size, color) -> str:
        """Извлечение кастомизации из заказа"""
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
            print(
                Fore.GREEN
                + f"- Кастомизация:\n{Fore.MAGENTA}{customization}{Back.WHITE}"
                + Back.WHITE
            )
            return customization

        except AttributeError:
            print(
                Fore.YELLOW
                + "||| Не смог получить кастомизацию, возможно, она не указана |||"
                + Back.WHITE
            )
            return ""
        except ValueError as e:
            print(Fore.RED + f"||| Ошибка: {e} |||" + Back.WHITE)
            return ""

    def __get_material_from_sku(self) -> str | None:
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
        """Извлечение цвета из part number"""
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
        """Извлечение размера товара"""
        patterns = [
            r"\b(\d+)\s*x\s*(\d+)\b",  # 35x52
            r"\((\d+)\s*x\s*(\d+)\)",  # (9x14)
            r'(\d+)"?\s*[HhWw]\s*X\s*(\d+)"?\s*[HhWw]',  # 17" H X 22" W
        ]
        for pattern in patterns:
            match = re.search(pattern, self.sku, re.IGNORECASE)
            if match:
                return f"{match.group(1).strip()}x{match.group(2).strip()} inches"
        return None

    @staticmethod
    def __get_quantity(item) -> int | str:
        """Извлечение количества конкретного товара"""
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
            print(
                Fore.GREEN
                + f"- Количество: {Fore.MAGENTA}{quantity}{Back.WHITE}"
                + Back.WHITE
            )
            return int(quantity)
        except AttributeError:
            print(Fore.RED + "||| Не смог получить количество |||" + Back.WHITE)
            return "!ERROR!"

    def get_extension(self) -> str:
        """Получение расширения файла для последующей сортировки по листам"""
        files = self.__search_link_to_file()

        # Проверка, что возвращен список файлов
        if files and isinstance(files, list):
            for file in files:
                if file["name"] != "File Not Found":
                    extension = file["name"].split(".")[
                        -1
                    ]  # Получаем расширение первого подходящего файла
                    return extension
            return "Unknown"  # Если файлы есть, но не нашли нужный файл
        else:
            return "Unknown"

    def get_smaller_size(self) -> float | str:
        """Получение меньшего значения в размере товара для сортировки"""
        files = self.__search_link_to_file()
        try:
            if files and isinstance(files, list):
                for file in files:
                    if file["name"] != "File Not Found":
                        size_from_name = file["name"].split(" ")[0]
                        if "," in size_from_name:
                            size_from_name = size_from_name.replace(",", ".")
                        size = size_from_name.split("x")
                        width = float(size[0].strip())
                        height = float(size[1].strip())
                        smaller_size = min(width, height)
                        return float(smaller_size)
            print(
                Fore.RED
                + "||| Не смог получить меньший размер для сортировки |||"
                + Back.WHITE
            )
            return "!ERROR!"
        except (ValueError, AttributeError):
            print(
                Fore.RED
                + "||| Не смог получить меньший размер для сортировки |||"
                + Back.WHITE
            )
            return "!ERROR!"
