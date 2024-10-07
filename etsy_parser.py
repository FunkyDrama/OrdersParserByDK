import datetime
import re

from bs4 import BeautifulSoup as Soup
from colorama import Fore, Back

from gdrive_finder import GoogleDriveFinder


class EtsyParser(GoogleDriveFinder):
    """Класс для парсинга данных из заказа. Наследует методы GoogleDriveFinder"""

    def __init__(self, order):
        """Инициализация переменных данных заказов и метода Soup"""
        super().__init__()
        self.order = order
        self.soup = Soup(order, "lxml")
        self.date = None
        self.listing_link = None
        self.store_title = None
        self.order_id = None
        self.listing_title = None
        self.sku = None
        self.address = None
        self.customization = None
        self.quantity = None
        self.items_total = None
        self.shipping_total = None
        self.postal_service = None
        self.tracking_number = None
        self.tracking_link = None
        self.shipping_type = None
        self.shipping_label_link = None
        self.file_link = None
        self.size = None
        self.shipping_price = None

    @staticmethod
    def get_parse_date(self):
        """Метод получения сегодняшней даты"""
        self.today = datetime.date.today().strftime("%d.%m.%Y")
        print(Fore.GREEN + f'- Дата обработки заказа: {Fore.MAGENTA}{self.today}{Back.WHITE}' + Back.WHITE)
        return self.today

    @staticmethod
    def search_link_to_file(self):
        """Метод поиска ссылки на файл по номеру заказа или SKU"""
        file_link = self.search_file_by_name(self,
                                             query=f"name contains '{self.order_id}' and not name contains '.pdf'")
        if file_link is None:
            file_link = self.search_file_by_name(self, query=f"name contains '{self.sku}' and not name contains '.pdf'")
        return file_link

    def parse_order(self):
        """Метод парсинга данных из заказа"""
        self.date = self.get_parse_date(self)
        self.listing_link = self.get_listing_link()
        self.store_title = self.get_store_title()
        self.order_id = self.get_order_id()
        self.listing_title = self.get_listing_title()
        self.sku = self.get_sku()
        self.address = self.get_address()
        self.customization = self.get_customization()
        self.quantity = self.get_quantity()
        self.items_total = self.get_items_total()
        self.shipping_total = self.get_shipping_total_value()
        self.shipping_price = self.get_shipping_price()
        self.postal_service = self.get_postal_service()
        self.tracking_number = self.get_tracking_number()
        self.tracking_link = self.get_tracking_link()
        self.shipping_type = self.get_shipping_type()
        # Поиск ссылки на шиплейбл. Если не найдено, в таблицу будет вставлен текст File Not Found
        file_result = self.search_file_by_name(self, query=f"name contains '{self.order_id}' and name contains '.pdf'")
        self.shipping_label_link = file_result['link'] if file_result else 'File Not Found'
        # Поиск ссылки на файл. Если не найдено, в таблицу будет вставлен текст File Not Found
        file_result = self.search_link_to_file(self)
        self.file_link = file_result['link'] if file_result else 'File Not Found'
        self.size = self.get_size()
        order_data = {
            'Status': None,
            'Date': self.date,
            'Store': self.store_title,
            'Channel': 'Etsy',
            'ASIN/SKU': self.sku,
            'Listing Link': self.listing_link,
            'Order ID': self.order_id,
            'Title': self.listing_title,
            'Address/Ship to': self.address,
            'Quantity': self.quantity,
            'Customization info': self.customization,
            'File Link': self.file_link,
            'Shipping label link': self.shipping_label_link,
            'Track ID': self.tracking_number,
            'Postal Service': self.postal_service,
            'Shipping speed': self.shipping_type,
            'Track package': self.tracking_link,
            'Items total': self.items_total,
            'Shipping total': self.shipping_total,
            'Shipping price': self.shipping_price,
            'Total': (self.items_total + self.shipping_price) - self.shipping_total
        }
        return order_data

    def get_smaller_size(self):
        """Получение меньшего значения в размере товара для сортировки"""
        try:
            size = self.size.split("x")
            width = size[0]
            height = size[1]
            smaller_size = min(width, height)
            return int(smaller_size)
        except AttributeError:
            print(Fore.RED + "||| Не смог получить меньший размер для сортировки |||" + Back.WHITE)
            return "!ERROR!"

    def get_extension(self):
        """Получение расширения файла для последующей сортировки по листам"""
        file_link = self.search_link_to_file(self)
        if file_link['name'] != 'File Not Found':
            extension = self.search_link_to_file(self)['name'].split(".")[-1]
        else:
            extension = 'Unknown'

        return extension

    def get_listing_link(self):
        """Извлечение и преобразование ссылки. Должна быть вставлена перед заказом"""
        try:
            listing_url_match = re.search(r'(https://www\.etsy\.com/listing/[^?\s]+)', self.order)
            listing_url = listing_url_match.group(1)
            print(Fore.GREEN + f'- Ссылка на листинг: {Fore.MAGENTA}{listing_url}{Back.WHITE}' + Back.WHITE)
            return listing_url
        except AttributeError:
            print(
                Fore.RED + "||| Не смог получить ссылку на листинг. Скорее всего, она не была добавлена |||" + Back.WHITE)
            return "!ERROR!"

    def get_store_title(self):
        """Извлечение названия магазина"""
        try:
            store_title = (self.soup.find("span", id="order-details-order-info", class_="display-inline-block").
                           find("a", classname="text-gray-darker").text.strip())
            print(Fore.GREEN + f'- Название магазина: {Fore.MAGENTA}{store_title}{Back.WHITE}' + Back.WHITE)
            return store_title
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название магазина |||" + Back.WHITE)
            return "!ERROR!"

    def get_order_id(self):
        """Извлечение номера заказа"""
        try:
            order_id = (self.soup.find("span", id="order-details-order-info", class_="display-inline-block").
                        find("a", classname="strong").text.strip())
            print(Fore.GREEN + f'- Номер заказа: {Fore.MAGENTA}{order_id}{Back.WHITE}' + Back.WHITE)
            return order_id
        except AttributeError:
            print(Fore.RED + "||| Не смог получить номер заказа |||" + Back.WHITE)
            return "!ERROR!"

    def get_listing_title(self):
        """Извлечение названия товара"""
        try:
            customizations_div = (self.soup.
                                  find("div", class_="flag-body prose").
                                  find_all_next("span", {'data-test-id': 'unsanitize'}))

            listing_title = customizations_div[0].text.strip()
            print(Fore.GREEN + f" - Название товара: {Fore.MAGENTA}{listing_title}{Back.WHITE}" + Back.WHITE)
            return listing_title
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название листинга |||" + Back.WHITE)
            return "!ERROR!"

    def get_sku(self):
        """Извлечение SKU"""
        sku_in_title = self.listing_title.split(" ")[-1]
        try:
            sku = (self.soup.find("div", class_="flag-body prose").find_next("span", class_="mb-xs-1").find("p").
                   find("span", {'data-test-id': 'unsanitize'})).text.strip()
        except AttributeError:
            print(Fore.YELLOW + 'SKU не указан на листинге, пытаюсь получить его из названия товара' + Back.WHITE)
            sku = sku_in_title
        print(Fore.GREEN + f'- SKU товара: {Fore.MAGENTA}{sku}{Back.WHITE}' + Back.WHITE)
        return sku

    def get_address(self):
        """Извлечение адреса"""
        try:
            address_div = self.soup.find("div", class_="address break-word").find("p")
            name = address_div.find("span", class_="name").text.strip()
            first_line = address_div.find("span", class_="first-line").text.strip()
            city = address_div.find("span", class_="city").text.strip()
            state = address_div.find("span", class_="state").text.strip()
            zip_code = address_div.find("span", class_="zip").text.strip()
            country_name = address_div.find("span", class_="country-name").text.strip()
            full_address = f"{name}\n{first_line}\n{city}, {state} {zip_code}\n{country_name}"
            print(Fore.GREEN + f'- Адрес клиента:\n{Fore.MAGENTA}{full_address}{Back.WHITE}' + Back.WHITE)
            return full_address
        except AttributeError:
            print(Fore.RED + "||| Не смог получить адрес клиент |||" + Back.WHITE)
            return "!ERROR!"

    def get_customization(self):
        """Извлечение и преобразование кастомизации из заказа"""
        customization_block = self.soup.find("div", class_="flag-body prose").find_all("li")
        customization_items = " \n".join([li.get_text() for li in customization_block])

        try:
            customer_info = (self.soup.find("div", class_="order-detail-buyer-note bg-blinding-sandstorm panel pointer"
                                                          " pointer-top-left text-body-smaller p-xs-2 mt-xs-2 mb-xs-0").
                             find("pre", class_="note").
                             find("span", {'data-test-id': 'unsanitize'})).text.strip()
            customization_items += f"\nBuyer Note: {customer_info}"
            print(Fore.GREEN + f'- Кастомизация:\n  {Fore.MAGENTA}{customization_items}{Back.WHITE}' + Back.WHITE)
        except AttributeError:
            customer_info = None

        return customization_items

    def get_size(self):
        """Извлечение размера товара"""
        try:
            size = self.soup.find("div", class_="flag-body prose").find_all("li")
            size = size[0].get_text().partition(' ')[2].rstrip(' inches')
            if "\"" in size:
                size = size.replace("\"", "")
            print(Fore.GREEN + f'- Размер товара: {Fore.MAGENTA}{size}{Back.WHITE}' + Back.WHITE)
            return size
        except AttributeError:
            print(Fore.RED + "||| Не смог получить размер товара |||" + Back.WHITE)
            return "!ERROR!"

    def get_quantity(self):
        """Извлечение количества товара в заказе"""
        try:
            quantity = self.soup.find("td", class_="col-xs-2 pl-xs-0 text-center").text.strip()
            print(Fore.GREEN + f'- Количество: {Fore.MAGENTA}{quantity}{Back.WHITE}' + Back.WHITE)
            return quantity
        except AttributeError:
            print(Fore.RED + "||| Не смог получить количество |||" + Back.WHITE)
            return "!ERROR!"

    def get_shipping_price(self):
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

    def get_items_total(self):
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

    def get_shipping_total_value(self):
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

    def get_postal_service(self):
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

    def get_tracking_number(self):
        """Извлечение трек-номера"""
        try:
            tracking_number = self.soup.find("div", class_="col-xs-9 wt-wrap").find("a").text.strip()
            print(Fore.GREEN + f'- Трек-номер: {Fore.MAGENTA}{tracking_number}{Back.WHITE}' + Back.WHITE)
            return tracking_number
        except AttributeError:
            print(Fore.RED + "||| Не смог получить трек-номер |||" + Back.WHITE)
            return "!ERROR!"

    def get_tracking_link(self):
        """Извлечение ссылки на отслеживание посылки"""
        try:
            tracking_link = self.soup.find("div", class_="col-xs-9 wt-wrap").find("a").get("href")
            print(Fore.GREEN + f'- Ссылка на отслеживание: {Fore.MAGENTA}{tracking_link}{Back.WHITE}' + Back.WHITE)
            return tracking_link
        except AttributeError:
            print(Fore.RED + "||| Не смог получить ссылку на отслеживание |||" + Back.WHITE)
            return "!ERROR"

    def get_shipping_type(self):
        """Извлечение типа доставки"""
        try:
            shipping_type = (self.soup.find("div", class_="strong text-body-smaller").
                             find("span", {'data-test-id': 'unsanitize'}).text.strip())
            print(Fore.GREEN + f'- Тип доставки: {Fore.MAGENTA}{shipping_type}{Back.WHITE}' + Back.WHITE)
            return shipping_type
        except AttributeError:
            print(Fore.RED + "||| Тип доставки не найден |||" + Back.WHITE)
            return "!ERROR!"
