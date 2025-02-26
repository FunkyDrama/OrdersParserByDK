from typing import Any
import datetime
import re
from colorama import Fore, Back

from google_api.gdrive_finder import GoogleDriveFinder
from bs4 import BeautifulSoup as Soup


class OverstockParser:
    def __init__(self, order: Any) -> None:
        self.order = order
        self.soup = Soup(order, "lxml")
        self.finder = GoogleDriveFinder()
        self.order_id = None
        self.sku = None

    def parse_order(self):
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
            files = [{'link': 'File Not Found', 'name': 'File Not Found'}]
        if shipping_label_link == "File Not Found":
            file_result = self.finder.search_file_by_name(
                query=f"name contains '{self.order_id}' and name contains '.pdf'")
            shipping_label_link = file_result[0]['link'] if file_result else 'File Not Found'

        order_items = []
        items = self.soup.find("table", class_="table table-hover data-table").find_all("td", id="lineProductCell")

        file_index = 0
        for item in items:
            listing_title = self.__get_listing_title(item)
            self.sku = self.__get_sku(item)
            size = self.__get_size(item)
            color = self.__get_color(item)
            customization = self.__get_customization(size, color)
            quantity = self.__get_quantity(item)

            listing_url = listing_links[items.index(item)] if items.index(item) < len(
                listing_links) else 'File Not Found'

            if file_index < len(files) and files[file_index]['name'] != 'File Not Found':
                file_link = files[file_index]['link']
                file_index += 1
            else:
                file_link = "File Not Found"

            order_data = {
                'Status': None,
                'Additional Info': None,
                'Date': date,
                'Store': store_title,
                'Channel': 'Overstock',
                'ASIN/SKU': self.sku,
                'Listing Link': listing_url,
                'Order ID': self.order_id,
                'Title': listing_title,
                'Address/Ship to': address,
                'Quantity': quantity,
                'Customization info': customization,
                'File Link': file_link,
                'Shipping label link': shipping_label_link,
                'Track ID': tracking_number,
                'Ship By': ship_by_date,
                'Postal Service': postal_service,
                'Shipping speed': shipping_type,
                'Track package': tracking_link,
                'Items total': items_total,
                'Shipping total': 0,
                'Shipping price': 0,
                'Total': items_total
            }
            order_items.append(order_data)

        return order_items

    @staticmethod
    def __get_parse_date(self) -> str:
        """Метод получения сегодняшней даты"""
        self.today = datetime.date.today().strftime("%d.%m.%Y")
        print(Fore.GREEN + f'- Дата обработки заказа: {Fore.MAGENTA}{self.today}{Back.WHITE}' + Back.WHITE)
        return self.today

    def __get_order_id(self) -> str | None | Any:
        """Извлечение номера заказа"""
        try:
            order_id_div = self.soup.find_all("div", id="soId")
            for el in order_id_div:
                if el.find("h6").text.strip() == "Retailer Order #":
                    order_id = el.find("p").text.strip()
                    print(Fore.GREEN + f'- Номер заказа: {Fore.MAGENTA}{order_id}{Back.WHITE}' + Back.WHITE)
                    return order_id
        except AttributeError:
            print(Fore.RED + "||| Не смог получить номер заказа |||" + Back.WHITE)
            return "!ERROR!"

    def __get_store_title(self):
        """Извлечение названия магазина"""
        try:
            store_title = self.soup.find("div", id="soChannel").find("p").text.strip()
            print(Fore.GREEN + f'- Название магазина: {Fore.MAGENTA}{store_title}{Back.WHITE}' + Back.WHITE)
            return store_title
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название магазина |||" + Back.WHITE)
            return "!ERROR!"

    def __get_address(self) -> str | None:
        """Извлечение адреса"""
        try:
            address_block = self.soup.find("div", id="soShippingAddress").find("p")
            address_parts = [br.get_text(strip=True) for br in address_block]
            address = "\n".join(address_parts.strip() for address_parts in address_parts if address_parts.strip())
            print(Fore.GREEN + f'- Адрес доставки:\n{Fore.MAGENTA}{address}{Back.WHITE}' + Back.WHITE)
            return address
        except AttributeError:
            print(Fore.RED + "||| Не смог получить адрес доставки |||" + Back.WHITE)
            return "!ERROR!"

    def __get_items_total(self) -> float | str:
        """Получение общей стоимости товара"""
        try:
            items_rows = self.soup.find_all("td", id="lineFirstCostCell")
            items_total = 0
            for row in items_rows:
                items_total += float(row.text.strip().replace('$', ''))

            print(Fore.GREEN + f'- Сумма заказа: {Fore.MAGENTA}{items_total}{Back.WHITE}' + Back.WHITE)
            return items_total
        except AttributeError:
            print(Fore.RED + "||| Не смог получить сумму заказа |||" + Back.WHITE)
            return "!ERROR!"

    def __search_link_to_file(self) -> list[dict[str, Any]] | None:
        """Метод поиска ссылки на файл по номеру заказа или SKU"""
        file_link = self.finder.search_file_by_name(
            query=f"name contains '{self.order_id}' and not name contains '.pdf'")
        if file_link is None:
            file_link = self.finder.search_file_by_name(
                query=f"name contains '{self.sku}' and not name contains '.pdf'")
        return file_link

    def __get_listing_links(self) -> list[str]:
        """Извлечение и преобразование всех ссылок на листинги из заказа"""
        listing_urls = []
        try:
            listing_url_matches = re.finditer(
                r'(https://www\.(?:overstock|bedbathandbeyond)\.com/[^?\s]+)', self.order
            )
            for match in listing_url_matches:
                listing_url = match.group(1)
                listing_urls.append(listing_url)
                print(Fore.GREEN + f'- Ссылка на листинг: {Fore.MAGENTA}{listing_url}{Back.WHITE}' + Back.WHITE)

            if not listing_urls:
                print(Fore.RED + "||| Не найдено ни одной ссылки на листинг |||" + Back.WHITE)
                return ["!ERROR!"]

            return listing_urls
        except Exception as e:
            print(Fore.RED + f"||| Ошибка при получении ссылок на листинги: {e} |||" + Back.WHITE)
            return ["!ERROR!"]

    @staticmethod
    def __get_listing_title(item) -> str:
        """Извлечение названия товара"""
        try:
            listing_title = item.find("p", class_="listing-title")
            if listing_title:
                listing_title = listing_title.text.strip()
            print(Fore.GREEN + f"- Название товара: {Fore.MAGENTA}{listing_title}{Back.WHITE}" + Back.WHITE)
            return listing_title
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название листинга |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_sku(item) -> str:
        """Извлечение SKU"""
        try:
            sku = item.find("div").text.strip()
            print(Fore.GREEN + f"- SKU товара: {Fore.MAGENTA}{sku}{Back.WHITE}" + Back.WHITE)
            return sku
        except AttributeError:
            print(Fore.RED + "||| Не смог получить SKU |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_size(item) -> str | None:
        """Извлечение размера товара"""
        patterns = [
            r'\b(\d+)\s*x\s*(\d+)\b',  # 35x52
            r'\((\d+)\s*x\s*(\d+)\)',  # (9x14)
            r'(\d+)"?\s*[HhWw]\s*X\s*(\d+)"?\s*[HhWw]',  # 17" H X 22" W
            r'(\d+)\s*inches\s*(\d+)\s*inches'  # 22 inches 26 inches
        ]
        for pattern in patterns:
            match = re.search(pattern, item.text.strip(), re.IGNORECASE)
            if match:
                return f"{match.group(1).strip()}x{match.group(2).strip()} inches"
        return None

    @staticmethod
    def __get_color(item) -> str | None:
        """Извлечение цвета из part number"""
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
    def __get_customization(size, color) -> str:
        """Извлечение кастомизации из заказа"""
        try:
            customization_list = []

            if size:
                size_customization = f'Size: {size}'
                customization_list.append(size_customization)

            if color:
                color_customization = f'Color: {color.title().strip()}'
                customization_list.append(color_customization)

            customization = "\n".join(customization_list)
            print(Fore.GREEN + f"- Кастомизация:\n{Fore.MAGENTA}{customization}{Back.WHITE}" + Back.WHITE)
            return customization

        except AttributeError:
            print(Fore.YELLOW + "||| Не смог получить кастомизацию, возможно, она не указана |||" + Back.WHITE)
            return ""
        except ValueError as e:
            print(Fore.RED + f"||| Ошибка: {e} |||" + Back.WHITE)
            return ""

    @staticmethod
    def __get_quantity(item) -> int | str:
        """Извлечение количества конкретного товара"""
        try:
            quantity_cell = item.find_previous_sibling("td", id="lineQuantityCell")
            if quantity_cell:
                quantity = quantity_cell.text.strip()
                print(Fore.GREEN + f"- Количество: {Fore.MAGENTA}{quantity}{Back.WHITE}" + Back.WHITE)
                return int(quantity)
        except AttributeError:
            print(Fore.RED + "||| Не смог получить количество |||" + Back.WHITE)
        return "!ERROR!"

    def __get_postal_service(self) -> str:
        """Извлечение названия почтовой службы"""
        try:
            postal_service = self.soup.find_all("span", class_="carrierCode existing_carrier")[0].text.strip()
            print(Fore.GREEN + f'- Служба доставки: {Fore.MAGENTA}{postal_service}{Back.WHITE}' + Back.WHITE)
            return postal_service
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Не смог получить службу доставки |||" + Back.WHITE)
            return "!ERROR!"

    def __get_tracking_number(self) -> str:
        """Извлечение трек-номера"""
        try:
            tracking_number = self.soup.find_all("span", class_="existing_tracking_number")[0].text.strip()
            print(Fore.GREEN + f'- Трек-номер: {Fore.MAGENTA}{tracking_number}{Back.WHITE}' + Back.WHITE)
            return tracking_number
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Не смог получить трек-номер |||" + Back.WHITE)
            return "!ERROR!"

    def __get_tracking_link(self, postal_service: str, tracking_number: str) -> str | list[str] | None:
        """Извлечение ссылки на отслеживание посылки"""
        try:
            if postal_service == "USPS":
                tracking_link = f"https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1={tracking_number}"
                print(Fore.GREEN + f'- Ссылка на отслеживание: {Fore.MAGENTA}{tracking_link}{Back.WHITE}' + Back.WHITE)
                return tracking_link
            elif postal_service == "UPS":
                tracking_link = f"https://www.ups.com/track?TypeOfInquiryNumber=T&InquiryNumber1={tracking_number}&loc=en_US&requester=ST/trackdetails"
                print(Fore.GREEN + f'- Ссылка на отслеживание: {Fore.MAGENTA}{tracking_link}{Back.WHITE}' + Back.WHITE)
                return tracking_link
            elif postal_service == "FedEx":
                tracking_link = f"https://www.fedex.com/apps/fedextrack/?tracknumbers={tracking_number}"
                print(Fore.GREEN + f'- Ссылка на отслеживание: {Fore.MAGENTA}{tracking_link}{Back.WHITE}' + Back.WHITE)
                return tracking_link
            elif postal_service == "DHL":
                tracking_link = f"https://www.dhl.com/us-en/home/tracking/tracking-express.html?submit=1&tracking-id={tracking_number}"
                print(Fore.GREEN + f'- Ссылка на отслеживание: {Fore.MAGENTA}{tracking_link}{Back.WHITE}' + Back.WHITE)
                return tracking_link
            else:
                tracking_link = self.soup.find_all("div", class_="existingShipments")[0].find("a").get("href")
                return tracking_link
        except AttributeError:
            print(Fore.RED + "||| Не смог получить ссылку на отслеживание |||" + Back.WHITE)
            return "!ERROR!"

    def __get_shipping_type(self) -> str:
        """Извлечение типа доставки"""
        try:
            shipping_type = self.soup.find("div", id="soShipMethod").find("p").text.strip()
            print(Fore.GREEN + f'- Тип доставки: {Fore.MAGENTA}{shipping_type}{Back.WHITE}' + Back.WHITE)
            return shipping_type
        except AttributeError:
            print(Fore.RED + "||| Не смог получить тип доставки |||" + Back.WHITE)
            return "!ERROR!"

    def __ship_by_date(self) -> str:
        """Извлечение крайней даты отправки посылки"""
        try:
            ship_by_date_div = self.soup.find_all("div", class_="existingShipments")[0]
            text = ship_by_date_div.get_text(" ", strip=True)
            match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', text)
            if match:
                ship_by_date = match.group(1)
                formatted_date = datetime.datetime.strptime(ship_by_date, "%m/%d/%Y").strftime("%d.%m.%Y")
                print(Fore.GREEN + f'- Заказ отправить до: {Fore.MAGENTA}{formatted_date}{Back.WHITE}' + Back.WHITE)
                return formatted_date
            return self.__get_parse_date(self)
        except (AttributeError, IndexError):
            formatted_date = self.__get_parse_date(self)
            print(Fore.GREEN + f'- Заказ отправить до: {Fore.MAGENTA}{formatted_date}{Back.WHITE}' + Back.WHITE)
            return formatted_date

    def get_extension(self) -> str:
        """Получение расширения файла для последующей сортировки по листам"""
        files = self.__search_link_to_file()

        # Проверка, что возвращен список файлов
        if files and isinstance(files, list):
            for file in files:
                if file['name'] != 'File Not Found':
                    extension = file['name'].split(".")[-1]  # Получаем расширение первого подходящего файла
                    return extension
            return 'Unknown'  # Если файлы есть, но не нашли нужный файл
        else:
            return 'Unknown'

    def get_smaller_size(self) -> float | str:
        """Получение меньшего значения в размере товара для сортировки"""
        files = self.__search_link_to_file()
        try:
            if files and isinstance(files, list):
                for file in files:
                    if file['name'] != 'File Not Found':
                        size_from_name = file['name'].split(" ")[0]
                        if "," in size_from_name:
                            size_from_name = size_from_name.replace(",", ".")
                        size = size_from_name.split("x")
                        width = float(size[0].strip())
                        height = float(size[1].strip())
                        smaller_size = min(width, height)
                        return float(smaller_size)
            print(Fore.RED + "||| Не смог получить меньший размер для сортировки |||" + Back.WHITE)
            return "!ERROR!"
        except (ValueError, AttributeError):
            print(Fore.RED + "||| Не смог получить меньший размер для сортировки |||" + Back.WHITE)
            return "!ERROR!"
