import datetime
from typing import Any, LiteralString

from bs4 import BeautifulSoup as Soup
from colorama import Fore, Back

from google_api.gdrive_finder import GoogleDriveFinder


class AmazonParser:
    def __init__(self, order: Any) -> None:
        self.order = order
        self.soup = Soup(order, "lxml")
        self.finder = GoogleDriveFinder()
        self.sku = None
        self.order_id = None
        self.size = None

    def parse_order(self) -> list[dict[str, None | str | int]]:
        """Метод парсинга заказа"""
        self.order_id = self.__get_order_id()
        date = self.__get_parse_date(self)
        store_title = self.__get_store_title()
        shipping_label_link = self.finder.upload_shipping_labels(self.order_id)
        address = self.__get_address()
        items_total = self.__get_items_total()
        shipping_total = self.__get_shipping_total_value()
        shipping_price = self.__get_shipping_price()
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
        items = self.soup.find('table', class_="a-keyvalue").find('tbody').find_all('tr')

        file_index = 0
        for item in items:
            listing_title = self.__get_listing_title(item)
            listing_link = self.__get_listing_link(item)
            self.sku = self.__get_sku(listing_title)
            quantity = self.__get_quantity(item)
            customization = self.__get_customization(item)

            # file_link = "File Not Found"
            # for file in files:
            #     if file['name'] != 'File Not Found':
            #         file_link = file['link']
            #         break
            if file_index < len(files) and files[file_index]['name'] != 'File Not Found':
                file_link = files[file_index]['link']
                file_index += 1
            else:
                file_link = "File Not Found"

            order_data = {
                'Status': None,
                'Additional Info': shipping_type if not (shipping_type.startswith("Standard")
                                                         or shipping_type.startswith("Free")) else None,
                'Date': date,
                'Store': store_title,
                'Channel': 'Amazon',
                'ASIN/SKU': self.sku,
                'Listing Link': listing_link,
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
                'Shipping total': shipping_total,
                'Shipping price': shipping_price,
                'Total': (items_total + shipping_price) - shipping_total
            }
            order_items.append(order_data)

        return order_items

    @staticmethod
    def __get_parse_date(self) -> str:
        """Метод получения сегодняшней даты"""
        self.today = datetime.date.today().strftime("%d.%m.%Y")
        print(Fore.GREEN + f'- Дата обработки заказа: {Fore.MAGENTA}{self.today}{Back.WHITE}' + Back.WHITE)
        return self.today

    def __get_store_title(self) -> str:
        """Извлечение названия магазина"""
        try:
            try:
                store_title = (self.soup.find("div", class_="dropdown-account-switcher-header-label").
                               find("span", class_="dropdown-account-switcher-header-label-global").text.strip())
                print(Fore.GREEN + f'- Название магазина: {Fore.MAGENTA}{store_title}{Back.WHITE}' + Back.WHITE)
                return store_title
            except AttributeError:
                store_title = (self.soup.find("button", class_="partner-dropdown-button").find("span").
                               find("b").text.strip())
                print(Fore.GREEN + f'- Название магазина: {Fore.MAGENTA}{store_title}{Back.WHITE}' + Back.WHITE)
                return store_title
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название магазина |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_sku(listing_title: str) -> str:
        """Извлечение SKU"""
        if "(" in listing_title:
            sku_with_brackets = listing_title.split(" (")[0].strip()
            sku = sku_with_brackets.split(" ")[-1].strip()
        else:
            sku = listing_title.split(" ")[-1].strip()
            if len(sku) == 1:
                sku = listing_title.split(" ")[-2].strip()
        print(Fore.YELLOW + 'SKU был взять из названия, проверьте после добавления в таблицу!' + Back.WHITE)
        print(Fore.GREEN + f'- SKU товара: {Fore.MAGENTA}{sku}{Back.WHITE}' + Back.WHITE)
        return sku

    @staticmethod
    def __get_listing_link(item: Any) -> str | None:
        """Извлечение ссылок на листинги"""
        try:
            # Найти элемент <a> непосредственно внутри <td>, содержащего ссылку
            link = item.find("a", href=True)  # Находим первый элемент <a> с атрибутом href
            if link:
                listing_link = link.get("href").strip()
                print(Fore.GREEN + f'- Ссылка на листинг: {Fore.MAGENTA}{listing_link}{Back.WHITE}' + Back.WHITE)
                return listing_link
            else:
                print(Fore.RED + "||| Не смог найти ссылку на листинг |||" + Back.WHITE)
                return None
        except Exception as e:
            print(Fore.RED + f"||| Ошибка при поиске ссылки на листинг: {str(e)} |||" + Back.WHITE)
            return None

    def __get_order_id(self) -> str:
        """Извлечение номера заказа"""
        try:
            order_id = (self.soup.find("div", class_="a-row a-spacing-mini").
                        find("span", {'data-test-id': 'order-id-value'}, class_="a-text-bold").text.strip())
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
                             find("div", class_="more-info-column-word-wrap-break-word").text.strip("\""))
            print(Fore.GREEN + f" - Название товара: {Fore.MAGENTA}{listing_title}{Back.WHITE}" + Back.WHITE)
            return listing_title
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название листинга |||" + Back.WHITE)
            return "!ERROR!"

    def __get_address(self) -> str:
        """Универсальное извлечение и форматирование адреса клиента в несколько строк"""
        try:
            # Найти div с адресом
            address_div = self.soup.find("div", {"data-test-id": "shipping-section-buyer-address"})

            # Безопасно попытаться найти номер телефона
            phone_number_tag = self.soup.find("span", {"data-test-id": "shipping-section-phone"})
            phone_number = phone_number_tag.text.strip() if phone_number_tag else None

            try:
                address_parts = []

                # Проходим по элементам внутри div, обрабатываем <span> и текстовые узлы
                for part in address_div.children:
                    if isinstance(part, str) and part.strip() == '':
                        continue

                    text = part.get_text(strip=True).replace(u'\xa0', ' ')
                    if text:
                        address_parts.append(text)

                # Форматирование адреса в зависимости от количества частей
                if len(address_parts) == 4:
                    full_address = f'{address_parts[0]}\n{address_parts[1]} {address_parts[2]} {address_parts[3]}'
                elif len(address_parts) == 5:
                    street_address = '\n'.join(address_parts[:-2])
                    city_state_zip = f'{address_parts[-2]} {address_parts[-1]}'
                    full_address = f'{street_address} {city_state_zip}'
                elif len(address_parts) > 5:
                    street_address = '\n'.join(address_parts[:-3])
                    city_state_zip = f'{address_parts[-3]} {address_parts[-2]}\n{address_parts[-1]}'
                    full_address = f'{street_address} {city_state_zip}'
                else:
                    full_address = '\n'.join(address_parts)

                # Если номер телефона найден, добавляем его в адрес
                if phone_number:
                    full_address += f'\nPhone: {phone_number}'

                print(Fore.GREEN + f'- Адрес клиента:\n{Fore.MAGENTA}{full_address}' + Fore.RESET)
                return full_address

            except IndexError:
                print(Fore.RED + "||| Адрес слишком длинный/короткий, не удалось обработать |||" + Fore.RESET)
                return "!ERROR!"

        except AttributeError:
            print(Fore.RED + "||| Не смог получить адрес клиента |||" + Fore.RESET)
            return "!ERROR!"

    @staticmethod
    def __get_quantity(item: Any) -> int | str:
        """Извлечение количества конкретного товара"""
        try:
            quantity_td = item.find("td", text=True)
            quantity = quantity_td.text.strip()
            print(Fore.GREEN + f'- Количество: {Fore.MAGENTA}{quantity}{Back.WHITE}' + Back.WHITE)
            return int(quantity)
        except AttributeError:
            print(Fore.RED + "||| Не смог получить количество |||" + Back.WHITE)
            return "!ERROR!"

    @staticmethod
    def __get_customization(item: Any) -> LiteralString | str:
        """Извлечение кастомизации из заказа"""
        try:
            customization_block = item.find("div", class_="a-row a-expander-container a-expander-extend-container")
            customization_items = ''.join(
                [line.text + '\n' for line in customization_block.find_all('div')][3::]).replace('\xa0', ' ')
            print(Fore.GREEN + f'- Кастомизация:\n{Fore.MAGENTA}{customization_items}{Back.WHITE}' + Back.WHITE)
            return customization_items.strip()
        except AttributeError:
            print(Fore.YELLOW + "||| Не смог получить кастомизацию, возможно, она не указана |||" + Back.WHITE)
            return ""

    def __search_link_to_file(self) -> list[dict[str, Any]] | None:
        """Метод поиска ссылки на файл по номеру заказа или SKU"""
        file_link = self.finder.search_file_by_name(
            query=f"name contains '{self.order_id}' and not name contains '.pdf'")
        if file_link is None:
            file_link = self.finder.search_file_by_name(
                query=f"name contains '{self.sku}' and not name contains '.pdf'")
        return file_link

    def __get_items_total(self) -> float | str:
        """Получение общей стоимости товара"""
        try:
            items_total = (
                self.soup.find("div", class_="a-row a-spacing-none order-details-bordered-box-sale-proceeds").
                find("td", class_="a-text-right a-align-bottom").find("span", class_="a-color-").text.strip())
            if items_total.startswith("CA"):
                items_total = items_total.replace("CA", "")
            items_total = float(items_total.strip("$"))
            print(Fore.GREEN + f'- Общая сумма за товары: {Fore.MAGENTA}{items_total}{Back.WHITE}' + Back.WHITE)
            return items_total
        except AttributeError:
            print(Fore.RED + "||| Не смог получить общую сумму за товары |||" + Back.WHITE)
            return 0

    def __get_shipping_total_value(self) -> float | str:
        """Получение стоимости, которую заплатил продавец за шиплейбл"""
        try:
            shipping_values = self.soup.find("div", class_="a-box-group a-spacing-top-micro").find(
                "span", class_="a-color-")
            total_shipping = shipping_values.text.strip("$")

            print(
                Fore.GREEN + f'- Сумма, уплаченная нами за доставку: {Fore.MAGENTA}{total_shipping}{Back.WHITE}' + Back.WHITE)
            return float(total_shipping)
        except (AttributeError, ValueError):
            print(Fore.RED + "||| Не смог получить сумму, уплаченную нами за доставку |||" + Back.WHITE)
            return 0

    def __get_shipping_price(self) -> float | int:
        """Цена доставки, которую заплатил клиент"""
        try:
            order_total = self.soup.find("div", class_="a-row a-spacing-none order-details-bordered-box-sale-proceeds")
            if "Shipping total" in order_total.text:
                shipping_total = order_total.find_all("td")[3].find("span", class_="a-color-").text.strip()
                if shipping_total.startswith("CA"):
                    shipping_total = shipping_total.replace("CA", "")
                shipping_price_value = float(shipping_total.strip("$"))
            else:
                shipping_price_value = 0
            print(
                Fore.GREEN + f'- Установленная цена за доставку: {Fore.MAGENTA}{shipping_price_value}{Back.WHITE}' + Back.WHITE)
            return shipping_price_value
        except (AttributeError, IndexError):
            print(Fore.RED + "||| Установленная цена за доставку не найдена |||" + Back.WHITE)
            return 0

    def __ship_by_date(self) -> str:
        """Извлечение крайней даты отправки посылки"""
        try:
            div = self.soup.find("div", class_="a-box-group a-spacing-top-micro")
            date_div = div.find_all('div', class_="a-column a-span3")[0].text.strip()
            if date_div:
                formatted_date = datetime.datetime.strptime(date_div, "%a, %b %d, %Y").strftime("%d.%m.%Y")
            else:
                formatted_date = self.__get_parse_date(self)
            print(Fore.GREEN + f'- Заказ отправить до: {Fore.MAGENTA}{formatted_date}{Back.WHITE}' + Back.WHITE)
            return formatted_date
        except AttributeError:
            formatted_date = self.__get_parse_date(self)
            print(Fore.GREEN + f'- Заказ отправить до: {Fore.MAGENTA}{formatted_date}{Back.WHITE}' + Back.WHITE)
            return formatted_date

    def __get_postal_service(self) -> str:
        """Извлечение названия почтовой службы"""
        try:
            postal_service_divs = self.soup.find("div", class_="a-box-group a-spacing-top-micro")
            postal_service = postal_service_divs.find_all('div', class_="a-column a-span3")[1].text.strip()
            print(Fore.GREEN + f'- Название почтовой службы: {Fore.MAGENTA}{postal_service}{Back.WHITE}' + Back.WHITE)
            return postal_service
        except AttributeError:
            print(Fore.RED + "||| Не смог получить название почтовой службы |||" + Back.WHITE)
            return "!ERROR!"

    def __get_tracking_number(self) -> str:
        """Извлечение трек-номера"""
        tracking_number = self.soup.find("a", class_="a-popover-trigger a-declarative",
                                         attrs={"data-test-id": "tracking-id-value"})
        if tracking_number:
            tracking_number = tracking_number.text.strip()
            print(Fore.GREEN + f'- Трек-номер: {Fore.MAGENTA}{tracking_number}{Back.WHITE}' + Back.WHITE)
            return tracking_number

        tracking_number = self.soup.find("span", attrs={"data-test-id": "tracking-id-value"})
        if tracking_number:
            tracking_number = tracking_number.text.strip()
            print(
                Fore.GREEN + f'- Трек-номер, если шиплейбл куплен не на Амазон: {Fore.MAGENTA}{tracking_number}{Back.WHITE}' + Back.WHITE)
            return tracking_number
        print(Fore.RED + "||| Не смог получить трек-номер |||" + Back.WHITE)
        return "!ERROR!"

    @staticmethod
    def __get_tracking_link(postal_service: str, tracking_number: str) -> str:
        """Извлечение ссылки на отслеживание посылки"""
        try:
            if postal_service == "USPS":
                tracking_link = f"https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1={tracking_number}"
                print(Fore.GREEN + f'- Ссылка на отслеживание: {Fore.MAGENTA}{tracking_link}{Back.WHITE}' + Back.WHITE)
                return tracking_link
            elif postal_service == "UPS" or postal_service == "UPS®":
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
        except AttributeError:
            print(Fore.RED + "||| Не смог получить ссылку на отслеживание |||" + Back.WHITE)
            return "!ERROR!"

    def __get_shipping_type(self) -> str:
        """Извлечение типа доставки"""
        try:
            shipping_type = (self.soup.find("span", {'data-test-id': 'order-summary-shipping-service-value'}).
                             find("span", class_="").text.strip())
            print(Fore.GREEN + f'- Тип доставки: {Fore.MAGENTA}{shipping_type}{Back.WHITE}' + Back.WHITE)
            return shipping_type
        except AttributeError:
            print(Fore.RED + "||| Тип доставки не найден |||" + Back.WHITE)
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
