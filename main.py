# pyinstaller --onefile --windowed --add-data "token.json:." --icon=icon.png --name=EtsyOrdersParserByDK main.py
import os
import sys

from colorama import Fore, init, Back

from etsy_parser import EtsyParser
from gsheet_writer import GSheetWriter

init(autoreset=True)


def main():
    """Основная функция, которая запускает программу"""
    print(Fore.CYAN + "--- Etsy Orders Parser v1.0 by Daniel K---" + Back.WHITE)

    def get_executable_dir():
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
            if "etsy.com" in order or "transaction_id" in order:
                print(Fore.GREEN + "----- Новый заказ Etsy-----" + Back.WHITE)
                etsy_parser = EtsyParser(order)
                order_data = etsy_parser.parse_order()
                extension = etsy_parser.get_extension()
                smaller_size = etsy_parser.get_smaller_size()
                writer = GSheetWriter()
                writer.sort_by_sheets(extension,  smaller_size)
                writer.append_order(order_data, extension, smaller_size)
            elif "amazon.com" in order or "Order ID" in order:
                print(Fore.LIGHTBLUE_EX + "----- Новый заказ Amazon-----" + Back.WHITE)


    print(Fore.CYAN + "<-- Все данные успешно добавлены. Проверьте внимательно данные в таблице! -->" + Back.WHITE)
    input(Fore.CYAN + "Нажмите Enter, чтобы выйти из программы..." + Back.WHITE)


if __name__ == "__main__":
    #os.chdir(sys._MEIPASS)
    main()
