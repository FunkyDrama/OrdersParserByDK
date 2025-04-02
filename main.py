# pyinstaller --onefile --windowed \
# --add-data="config/token.json:config" \
# --add-data="config/.env:config" \
# --add-data="google_api:google_api" \
# --add-data="marketplaces:marketplaces" \
# --icon=assets/icon.png \
# --hidden-import="pydantic_settings" \
# --hidden-import="pydantic" \
# --name=OrdersParserByDK \
# main.py

import os
import sys
from typing import LiteralString

from colorama import Fore, init, Back

from marketplaces.amazon_parser import AmazonParser
from marketplaces.ebay_parser import EbayParser
from marketplaces.etsy_parser import EtsyParser
from google_api.gsheet_writer import GSheetWriter
from marketplaces.overstock_parser import OverstockParser
from marketplaces.wayfair_parser import WayfairParser

init(autoreset=True)


def main() -> None:
    """Основная функция, которая запускает программу"""
    print(Fore.CYAN + "---Orders Parser v5.2 by Daniel K---" + Back.WHITE)

    def get_executable_dir() -> str | LiteralString:
        """ Возвращает путь к директории, где находится исполняемый файл или скрипт """
        if getattr(sys, 'frozen', False):
            # Если программа запущена как упакованный exe файл
            return os.path.dirname(sys.executable)
        else:
            # Если программа запущена как обычный скрипт
            return os.path.dirname(os.path.abspath(__file__))

    # Путь к orders.txt в той же директории, что и exe
    orders_path = os.path.join(get_executable_dir(), 'orders.txt')

    try:
        with open(orders_path, "r", encoding="utf-8") as f:
            orders_content = f.read()
    except FileNotFoundError:
        print(f"Файл {orders_path} не найден.")
        return

    orders = orders_content.split("</html>")

    for order in orders:
        if order.strip():
            if "etsy.com" in order in order:
                print(Fore.GREEN + "----- Новый заказ Etsy -----" + Back.WHITE)
                etsy_parser = EtsyParser(order)
                order_data = etsy_parser.parse_order()
                extension = etsy_parser.get_extension()
                smaller_size = etsy_parser.get_smaller_size()
                writer = GSheetWriter()
                writer.append_order(order_data, extension, smaller_size)
            elif "amazon.com" in order or "Order ID" in order:
                print(Fore.LIGHTBLUE_EX + "----- Новый заказ Amazon -----" + Back.WHITE)
                amazon_parser = AmazonParser(order)
                order_data = amazon_parser.parse_order()
                extension = amazon_parser.get_extension()
                smaller_size = amazon_parser.get_smaller_size()
                writer = GSheetWriter()
                writer.append_order(order_data, extension, smaller_size)
            elif "https://partners.wayfair.com/v/landing/index" in order:
                print(Fore.LIGHTMAGENTA_EX + "----- Новый заказ Wayfair -----" + Back.WHITE)
                wayfair_parser = WayfairParser(order)
                order_data = wayfair_parser.parse_order()
                extension = wayfair_parser.get_extension()
                smaller_size = wayfair_parser.get_smaller_size()
                writer = GSheetWriter()
                writer.append_order(order_data, extension, smaller_size)
            elif "https://edge.supplieroasis.com/dashboard/" in order:
                print(Fore.LIGHTYELLOW_EX + "----- Новый заказ Overstock -----" + Back.WHITE)
                overstock_parser = OverstockParser(order)
                order_data = overstock_parser.parse_order()
                extension = overstock_parser.get_extension()
                smaller_size = overstock_parser.get_smaller_size()
                writer = GSheetWriter()
                writer.append_order(order_data, extension, smaller_size)
            elif "https://www.ebay.com" in order:
                print(Fore.BLUE + "----- Новый заказ Ebay -----" + Back.WHITE)
                ebay_parser = EbayParser(order)
                order_data = ebay_parser.parse_order()
                extension = ebay_parser.get_extension()
                smaller_size = ebay_parser.get_smaller_size()
                writer = GSheetWriter()
                writer.append_order(order_data, extension, smaller_size)

    print(Fore.CYAN + "<-- Все данные успешно добавлены. Проверьте внимательно данные в таблице! -->" + Back.WHITE)
    input(Fore.CYAN + "Нажмите Enter, чтобы выйти из программы..." + Back.WHITE)


if __name__ == "__main__":
    # os.chdir(sys._MEIPASS)
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print(Fore.RED + "\nРабота программы была прервана пользователем." + Back.WHITE)
