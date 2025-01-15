from typing import List, Dict

import gspread
from colorama import Fore, Back
from google.oauth2 import service_account
from gspread import Worksheet
from gspread.utils import ValueInputOption

from config.settings import settings
from google_api.gdrive_finder import resource_path


class GSheetWriter:
    """Класс для записи данных в Google Sheets"""

    def __init__(self) -> None:
        """Инициализация данных Google Sheets и получение данных из заказа для последующей записи"""
        self.gspread_scope = ['https://www.googleapis.com/auth/spreadsheets']
        self.gspread_creds = service_account.Credentials.from_service_account_file(resource_path(
            'config/token.json'),
            scopes=self.gspread_scope)
        self.client = gspread.service_account('config/token.json')
        self.spreadsheet = self.client.open_by_key(settings.TABLE_ID)

    def __sort_by_sheets(self, extension: str, smaller_size: float | str) -> Worksheet:
        """Сортировка по листам, используя размер и расширение файла"""
        if not extension == 'Unknown':
            if extension in {"png", "jpg", "jpeg", "eps"}:
                worksheet = self.spreadsheet.worksheet("Colored")
                return worksheet
            # elif self.extension == "jpg":
            #     worksheet = self.spreadsheet.worksheet("Posters")
            #     return worksheet
            elif isinstance(smaller_size, float):
                if smaller_size <= 22 and not extension in {"png", "jpg", "eps", "jpeg"}:
                    worksheet = self.spreadsheet.worksheet("22 roll")
                    return worksheet
                elif smaller_size > 22 and not extension in {"png", "jpg", "eps", "jpeg"}:
                    worksheet = self.spreadsheet.worksheet("46 roll")
                    return worksheet

        print(Fore.YELLOW +
              '---Файл заказа не найден на диске, поэтому не смог определить расширение файла и отсортировать по листу.\n'
              'Заказ был добавлен на лист ERROR---' + Back.WHITE)
        worksheet = self.spreadsheet.worksheet("ERROR")
        return worksheet

    def append_order(self, order_items: List[Dict[str, None | str | int]], extension: str,
                     smaller_size: float | str) -> None:
        """Добавление данных в таблицу Google Sheets с закрашиванием ячеек, установкой стратегии обрезки текста и объединением ячеек"""

        worksheet = self.__sort_by_sheets(extension, smaller_size)
        headers = worksheet.row_values(1)  # Получаем заголовки первой строки

        # Получить количество строк с данными
        num_rows = len(worksheet.get_all_values())  # Получаем все строки, включая заголовки
        next_available_row = num_rows + 1  # Первая доступная строка для вставки данных

        # Найдем индексы нужных колонок
        order_id_col = headers.index('Order ID') + 1
        address_col = headers.index('Address/Ship to') + 1
        shipping_label_col = headers.index('Shipping label link') + 1
        track_id_col = headers.index('Track ID') + 1
        status_col_index = headers.index('Status') + 1

        # Добавляем индексы столбцов для объединения
        columns_to_merge = ['Postal Service', 'Shipping speed', 'Track package', 'Items total', 'Shipping total',
                            'Shipping price', 'Total']
        merge_col_indices = [headers.index(col) + 1 for col in columns_to_merge]

        # Цвет для ячеек в случае нескольких товаров
        multiple_order_cell_color = {
            "red": 0,
            "green": 0.6,
            "blue": 0
        }

        merge_requests = []

        for idx, order_item in enumerate(order_items):
            row_data = ['' for _ in range(len(headers))]  # Инициализация пустой строки для каждого товара

            # Заполнение данных в строку для каждого order_item
            for column, value in order_item.items():
                if column in headers:
                    col_index = headers.index(column)  # Найти индекс колонки по имени
                    row_data[col_index] = value  # Заполнить значение

            # Добавить строку данных в таблицу в первую доступную строку
            worksheet.insert_row(row_data, index=next_available_row, value_input_option=ValueInputOption.user_entered)
            new_row_index = next_available_row  # Текущая строка, куда добавлен товар
            next_available_row += 1  # Обновляем номер строки после вставки

            # Определяем цвет только если больше одного товара в заказе
            if len(order_items) > 1:
                # Закрашивание ячеек в нужных колонках
                worksheet.spreadsheet.batch_update({
                    "requests": [
                        {
                            "repeatCell": {
                                "range": {
                                    "sheetId": worksheet.id,
                                    "startRowIndex": new_row_index - 1,
                                    "endRowIndex": new_row_index,
                                    "startColumnIndex": col - 1,
                                    "endColumnIndex": col
                                },
                                "cell": {
                                    "userEnteredFormat": {
                                        "backgroundColor": multiple_order_cell_color
                                    }
                                },
                                "fields": "userEnteredFormat.backgroundColor"
                            }
                        } for col in [order_id_col, address_col, shipping_label_col, track_id_col]
                    ]
                })

                # Добавляем запросы на объединение ячеек
                for col_index in merge_col_indices:
                    if idx == 0:  # Только для первого товара в заказе
                        merge_requests.append({
                            "mergeCells": {
                                "range": {
                                    "sheetId": worksheet.id,
                                    "startRowIndex": new_row_index - 1,
                                    "endRowIndex": new_row_index - 1 + len(order_items),
                                    "startColumnIndex": col_index - 1,
                                    "endColumnIndex": col_index
                                },
                                "mergeType": "MERGE_ALL"
                            }
                        })

            # Установка стратегии обрезки текста (CLIP) для всей строки
            worksheet.spreadsheet.batch_update({
                "requests": [
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": worksheet.id,
                                "startRowIndex": new_row_index - 1,
                                "endRowIndex": new_row_index,
                                "startColumnIndex": 0,  # Начало строки (первый столбец)
                                "endColumnIndex": len(headers)  # Конец строки (все столбцы)
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "wrapStrategy": "CLIP"
                                }
                            },
                            "fields": "userEnteredFormat.wrapStrategy"
                        }
                    }
                ]
            })

            # Закрашивание колонки Status
            worksheet.spreadsheet.batch_update({
                "requests": [
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": worksheet.id,
                                "startRowIndex": new_row_index - 1,
                                "endRowIndex": new_row_index,
                                "startColumnIndex": status_col_index - 1,
                                "endColumnIndex": status_col_index
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {
                                        "red": 1.0,
                                        "green": 0.0,
                                        "blue": 0.0
                                    }
                                }
                            },
                            "fields": "userEnteredFormat.backgroundColor"
                        }
                    }
                ]
            })

        # Применяем все запросы на объединение ячеек
        if merge_requests:
            worksheet.spreadsheet.batch_update({"requests": merge_requests})

        print(Fore.GREEN + "\n<<<Заказ добавлен в таблицу>>>\n")
