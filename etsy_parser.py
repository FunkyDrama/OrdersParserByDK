import datetime
import re
from typing import Any, LiteralString

from bs4 import BeautifulSoup as Soup
from colorama import Fore, Back

from gdrive_finder import GoogleDriveFinder


class EtsyParser:
    """Класс для парсинга данных из заказа Etsy"""

    def __init__(self, order: Any):
        """Инициализация переменных данных заказов и метода Soup"""
        self.order = order
        self.soup = Soup(order, "lxml")
        self.finder = GoogleDriveFinder()
        self.sku = None
        self.order_id = None
        self.size = None

    @staticmethod
    def __get_parse_date(self) -> str:
        """Метод получения сегодняшней даты"""
        self.today = datetime.date.today().strftime("%d.%m.%Y")
        print(Fore.GREEN + f'- Дата обработки заказа: {Fore.MAGENTA}{self.today}{Back.WHITE}' + Back.WHITE)
        return self.today

    def __search_link_to_file(self) -> list[dict[str, Any]] | None:
        """Метод поиска ссылки на файл по номеру заказа или SKU"""
        file_link = self.finder.search_file_by_name(
            query=f"name contains '{self.order_id}' and not name contains '.pdf'")
        if file_link is None:
            file_link = self.finder.search_file_by_name(
                query=f"name contains '{self.sku}' and not name contains '.pdf'")
        return file_link

    def parse_order(self) -> list[dict[str, None | str | int]]:
        """Метод парсинга данных из заказа"""
        date = self.__get_parse_date(self)
        listing_links = self.__get_listing_links()
        store_title = self.__get_store_title()
        self.order_id = self.__get_order_id()
        address = self.__get_address()
        items_total = self.__get_items_total()
        shipping_total = self.__get_shipping_total_value()
        shipping_price = self.__get_shipping_price()
        postal_service = self.__get_postal_service()
        tracking_number = self.__get_tracking_number()
        tracking_link = self.__get_tracking_link()
        shipping_type = self.__get_shipping_type()

        # Поиск ссылки на шиплейбл. Если не найдено, в таблицу будет вставлен текст File Not Found
        file_result = self.finder.search_file_by_name(query=f"name contains '{self.order_id}' and name contains '.pdf'")
        shipping_label_link = file_result[0]['link'] if file_result else 'File Not Found'

        # Поиск всех файлов по размеру
        files = self.__search_link_to_file()
        if not files:
            files = [{'link': 'File Not Found', 'name': 'File Not Found'}]

        # Список для отслеживания назначенных файлов
        assigned_files = []

        order_items = []
        items = self.soup.find_all("tr", class_="col-group pl-xs-0 pt-xs-3 pr-xs-0 pb-xs-3 bb-xs-1")

        for index, item in enumerate(items):
            listing_title = self.__get_listing_title(item)
            self.sku = self.__get_sku(item, listing_title)
            customization = self.__get_customization(item)
            quantity = self.__get_quantity(item)
            self.size = self.__get_size(item)
            listing_url = listing_links[index] if index < len(listing_links) else 'File Not Found'

            matched_file_link = 'File Not Found'

            # Проход по файлам, чтобы найти подходящий файл по размеру
            for file_index, file in enumerate(files):
                # Извлечение чисел из имени файла и сравнение с размером товара
                file_name = file['name'].split('.')[0]
                file_size_match = re.findall(r'\d+\.?\d*', file_name.split(" ")[0])
                item_size_match = re.findall(r'\d+\.?\d*', self.size)

                # Если размеры совпадают и файл еще не был назначен товару
                if sorted(file_size_match) == sorted(item_size_match) and file_index not in assigned_files:
                    matched_file_link = file['link']
                    assigned_files.append(file_index)  # Отмечаем файл как назначенный
                    break

            order_data = {
                'Status': None,
                'Date': date,
                'Store': store_title,
                'Channel': 'Etsy',
                'ASIN/SKU': self.sku,
                'Listing Link': listing_url,
                'Order ID': self.order_id,
                'Title': listing_title,
                'Address/Ship to': address,
                'Quantity': quantity,
                'Customization info': customization,
                'File Link': matched_file_link,
                'Shipping label link': shipping_label_link,
                'Track ID': tracking_number,
                'Postal Service': postal_service,
                'Shipping speed': shipping_type,
                'Track package': tracking_link,
                'Items total': items_total,
                'Shipping total': shipping_total,
                'Shipping price': shipping_price,
                'Total': (items_total + shipping_price) - shipping_total
            }
            order_items.append(order_data)

        return order_items

    def get_smaller_size(self) -> int | str:
        """Получение меньшего значения в размере товара для сортировки"""
        try:
            size = self.size.split("x")
            width = int(size[0].strip())
            height = int(size[1].strip())
            smaller_size = min(width, height)
            return int(smaller_size)
        except AttributeError:
            print(Fore.RED + "||| Не смог получить меньший размер для сортировки |||" + Back.WHITE)
            return "!ERROR!"

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

    def __get_listing_links(self) -> list[str]:
        """Извлечение и преобразование всех ссылок на листинги из заказа"""
        listing_urls = []
        try:
            listing_url_matches = re.finditer(r'(https://www\.etsy\.com/listing/[^?\s]+)', self.order)
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

    def __get_store_title(self) -> str:
        """Извлечение названия магазина"""
        try:
            store_title = (self.soup.find("span", id="order-details-order-info", class_="display-inline-block").
                           find("a", classname="text-gray-darker").text.strip())
            print(Fore.GREEN + f'- Название магазина: {Fore.MAGENTA}{store_title}{Back.WHITE}' + Back.WHITE)
            return store_title
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название магазина |||" + Back.WHITE)
            return "!ERROR!"

    def __get_order_id(self) -> str:
        """Извлечение номера заказа"""
        try:
            order_id = (self.soup.find("span", id="order-details-order-info", class_="display-inline-block").
                        find("a", classname="strong").text.strip())
            print(Fore.GREEN + f'- Номер заказа: {Fore.MAGENTA}{order_id}{Back.WHITE}' + Back.WHITE)
            return order_id
        except AttributeError:
            print(Fore.RED + "||| Не смог получить номер заказа |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_listing_title(item: Any) -> str:
        """Извлечение названия товара"""
        try:
            listing_title = (item.
                             find("div", class_="flag-body prose").
                             find("span", {'data-test-id': 'unsanitize'})).text.strip()
            print(Fore.GREEN + f"- Название товара: {Fore.MAGENTA}{listing_title}{Back.WHITE}" + Back.WHITE)
            return listing_title
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название листинга |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_sku(item: Any, listing_title: str) -> str:
        """Извлечение SKU"""
        try:
            sku = item.find("span", class_="mb-xs-1").find("p").find("span",
                                                                     {'data-test-id': 'unsanitize'}).text.strip()
        except AttributeError:
            print(Fore.YELLOW + 'SKU не указан на листинге, пытаюсь получить его из названия товара' + Back.WHITE)
            sku = listing_title.split(" ")[-1]
        print(Fore.GREEN + f'- SKU товара: {Fore.MAGENTA}{sku}{Back.WHITE}' + Back.WHITE)
        return sku

    def __get_address(self) -> str:
        """Извлечение адреса"""
        try:
            address_div = self.soup.find("div", class_="address break-word").find("p")
            address_parts = {}

            # Поиск всех span элементов в адресе и распределение по ключам
            for span in address_div.find_all("span"):
                class_name = span.get("class", [None])[0]  # Получаем класс первого элемента, если он есть
                if class_name == "name":
                    address_parts['name'] = span.text.strip()
                elif class_name == "first-line":
                    address_parts['first_line'] = span.text.strip()
                elif class_name == "city":
                    address_parts['city'] = span.text.strip()
                elif class_name == "state":
                    address_parts['state'] = span.text.strip()
                elif class_name == "zip":
                    address_parts['zip_code'] = span.text.strip()
                elif class_name == "country-name":
                    address_parts['country_name'] = span.text.strip()

            # Составление полного адреса с проверкой наличия каждого элемента
            full_address = f"{address_parts.get('name', '')}\n{address_parts.get('first_line', '')}\n"
            full_address += f"{address_parts.get('city', '')}, {address_parts.get('state', '')} {address_parts.get('zip_code', '')}\n"
            full_address += f"{address_parts.get('country_name', '')}"

            print(Fore.GREEN + f'- Адрес клиента:\n{Fore.MAGENTA}{full_address}{Back.WHITE}' + Back.WHITE)
            return full_address

        except AttributeError:
            print(Fore.RED + "||| Не смог получить адрес клиента |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_customization(item: Any) -> LiteralString | None:
        """Извлечение и преобразование кастомизации из заказа"""
        customization_block = item.find("div", class_="flag-body prose").find_all("li")
        customization_items = " \n".join([li.get_text() for li in customization_block])

        try:
            customer_info = (item.find("div", class_="order-detail-buyer-note bg-blinding-sandstorm panel pointer"
                                                          " pointer-top-left text-body-smaller p-xs-2 mt-xs-2 mb-xs-0").
                             find("pre", class_="note").
                             find("span", {'data-test-id': 'unsanitize'})).text.strip()
            customization_items += f"\nBuyer Note: {customer_info}"
            print(Fore.GREEN + f'- Кастомизация:\n  {Fore.MAGENTA}{customization_items}{Back.WHITE}' + Back.WHITE)
        except AttributeError:
            customer_info = None

        return customization_items

    @staticmethod
    def __get_size(item: Any) -> str:
        """Извлечение размера товара"""
        try:
            size_text = item.find("div", class_="flag-body prose").find_all("li")[0].get_text()

            # Используем регулярное выражение для извлечения всех чисел (целых и дробных)
            size_pattern = re.findall(r'(\d+\.?\d*)', size_text)

            if size_pattern and len(size_pattern) >= 2:
                # Берем первые два числа, предполагая, что это ширина и высота
                width, height = size_pattern[:2]
                size = f"{width}x{height}"
                print(Fore.GREEN + f'- Размер товара: {Fore.MAGENTA}{size} inches{Back.WHITE}')
                return size
            else:
                print(Fore.YELLOW + "||| Не удалось распознать размер из текста: ", size_text, " |||" + Back.WHITE)
                return "!ERROR!"

        except AttributeError:
            print(Fore.RED + "||| Не смог получить размер товара |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_quantity(item: Any) -> int | str:
        """Извлечение количества товара в заказе"""
        try:
            quantity = item.find("td", class_="col-xs-2 pl-xs-0 text-center").text.strip()
            print(Fore.GREEN + f'- Количество: {Fore.MAGENTA}{quantity}{Back.WHITE}' + Back.WHITE)
            return int(quantity)
        except AttributeError:
            print(Fore.RED + "||| Не смог получить количество |||" + Back.WHITE)
            return "!ERROR!"

    def __get_shipping_price(self) -> float | str:
        """Цена доставки, которую заплатил клиент"""
        try:
            shipping_items = self.soup.find_all("li", class_="col-group wt-p-xs-0 wt-mt-xs-1 wt-mb-xs-1")

            for item in shipping_items:
                if "Shipping price" in item.text:
                    price_div = item.find("div", class_="col-xs-3 text-right wt-pr-xs-0")
                    shipping_price = price_div.text.strip()
                    shipping_price_value = float(shipping_price.strip("$"))
                    print(
                        Fore.GREEN + f'- Установленная цена за доставку: {Fore.MAGENTA}{shipping_price_value}{Back.WHITE}' + Back.WHITE)
                    return shipping_price_value
        except AttributeError:
            print(Fore.RED + "||| Установленная цена за доставку не найдена |||" + Back.WHITE)
            return "!ERROR!"

    def __get_items_total(self) -> float | str:
        """Получение общей стоимости товара"""
        try:
            items_total = (self.soup.find("li", class_="col-group wt-p-xs-0 wt-mt-xs-1 wt-mb-xs-1").
                           find_next("div", class_="col-xs-3 text-right wt-pr-xs-0").text.strip())
            items_total = float(items_total.strip("$"))
            print(Fore.GREEN + f'- Общая сумма за товары: {Fore.MAGENTA}{items_total}{Back.WHITE}' + Back.WHITE)
            return items_total
        except AttributeError:
            print(Fore.RED + "||| Не смог получить общую сумму за товары |||" + Back.WHITE)
            return "!ERROR!"

    def __get_shipping_total_value(self) -> int | str:
        """Получение стоимости, которую заплатил продавец за шиплейбл"""
        try:
            shipping_values = self.soup.find_all("div", class_="wt-flex-md-1 text-right")
            total_shipping = 0

            for value in shipping_values:
                values = value.find_all("strong", class_="mr-xs-1")
                for total in values:
                    shipping_cost = float(total.text.strip("$"))
                    total_shipping += shipping_cost

            print(
                Fore.GREEN + f'- Сумма, уплаченная нами за доставку: {Fore.MAGENTA}{total_shipping}{Back.WHITE}' + Back.WHITE)
            return total_shipping
        except (AttributeError, ValueError):
            print(Fore.RED + "||| Не смог получить сумму, уплаченную нами за доставку |||" + Back.WHITE)
            return "!ERROR!"

    def __get_postal_service(self) -> str:
        """Извлечение названия почтовой службы"""
        try:
            # Парсит название при покупке шиплейбла на Этси
            postal_service = self.soup.find("div", class_="text-truncate").find_next(
                "div", class_="pl-xs-1 mr-xs-2").find("p", class_="text-truncate").text.split(" ")[0]
            print(Fore.GREEN + f'- Название почтовой службы: {Fore.MAGENTA}{postal_service}{Back.WHITE}' + Back.WHITE)
            return postal_service
        except AttributeError:
            # Парсит название почтовой службы, если заказ был куплен на стороннем сервисе
            try:
                postal_service_div = self.soup.find_all("div", class_="display-inline-block")
                for el in postal_service_div:
                    paragraphs = el.find_all("p")
                    for p in paragraphs:
                        if "Shipping" in p.text:
                            postal_service = p.text.split(" ")[-1]

                            print(
                                Fore.GREEN + f'- Название почтовой службы (в случае, если доставка куплена не на Etsy): '
                                             f'{Fore.MAGENTA}{postal_service}{Back.WHITE}' + Back.WHITE)
                            return postal_service
            except AttributeError:
                # Если оба способа не сработали, возвращаем ошибку
                print(Fore.RED + "||| Не смог получить название почтовой службы |||" + Back.WHITE)
                return "!ERROR!"

    def __get_tracking_number(self) -> str:
        """Извлечение трек-номера"""
        try:
            tracking_number = self.soup.find("div", class_="col-xs-9 wt-wrap").find("a").text.strip()
            print(Fore.GREEN + f'- Трек-номер: {Fore.MAGENTA}{tracking_number}{Back.WHITE}' + Back.WHITE)
            return tracking_number
        except AttributeError:
            print(Fore.RED + "||| Не смог получить трек-номер |||" + Back.WHITE)
            return "!ERROR!"

    def __get_tracking_link(self) -> str | list[str] | None:
        """Извлечение ссылки на отслеживание посылки"""
        try:
            tracking_link = self.soup.find("div", class_="col-xs-9 wt-wrap").find("a").get("href")
            print(Fore.GREEN + f'- Ссылка на отслеживание: {Fore.MAGENTA}{tracking_link}{Back.WHITE}' + Back.WHITE)
            return tracking_link
        except AttributeError:
            print(Fore.RED + "||| Не смог получить ссылку на отслеживание |||" + Back.WHITE)
            return "!ERROR"

    def __get_shipping_type(self) -> str:
        """Извлечение типа доставки"""
        try:
            shipping_type = (self.soup.find("div", class_="strong text-body-smaller").
                             find("span", {'data-test-id': 'unsanitize'}).text.strip())
            print(Fore.GREEN + f'- Тип доставки: {Fore.MAGENTA}{shipping_type}{Back.WHITE}' + Back.WHITE)
            return shipping_type
        except AttributeError:
            print(Fore.RED + "||| Тип доставки не найден |||" + Back.WHITE)
            return "!ERROR!"
