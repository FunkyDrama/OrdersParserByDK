import gspread
from colorama import Fore, Back
from google.oauth2 import service_account

from gdrive_finder import resource_path


class GSheetWriter:
    """Класс для записи данных в Google Sheets. Наследуется от EtsyParser и соответственно от GoogleDriveFinder"""

    def __init__(self):
        """Инициализация данных Google Sheets и получение данных из заказа для последующей записи"""
        self.gspread_scope = ['https://www.googleapis.com/auth/spreadsheets']
        self.gspread_creds = service_account.Credentials.from_service_account_file(resource_path('token.json'),
                                                                                   scopes=self.gspread_scope)
        self.client = gspread.service_account('token.json')
        self.spreadsheet = self.client.open_by_key('1kZFamG8zkM-7-XpcB6FDlLBn_MT83Zuv1MS7Uy7jxpA')

    def sort_by_sheets(self, extension, smaller_size):
        """Сортировка по листам, используя размер и расширение файла"""
        if not extension == 'Unknown':
            if extension == "png" or extension == "jpg" or extension == "jpeg" or extension == "eps":
                worksheet = self.spreadsheet.worksheet("Colored")
                return worksheet
            # elif self.extension == "jpg":
            #     worksheet = self.spreadsheet.worksheet("Posters")
            #     return worksheet
            elif smaller_size <= 22 and not extension == "png" and not extension == "jpg" and not extension == "eps":
                worksheet = self.spreadsheet.worksheet("22 roll")
                return worksheet
            elif smaller_size > 22 and not extension == "png" and not extension == "jpg" and not extension == "eps":
                worksheet = self.spreadsheet.worksheet("46 roll")
                return worksheet
        else:
            print(Fore.YELLOW +
                  '---Файл заказа не найден на диске, поэтому не смог определить расширение файла и отсортировать по листу.\n'
                  'Заказ был добавлен на лист ERROR---' + Back.WHITE)
            worksheet = self.spreadsheet.worksheet("ERROR")
            return worksheet

    def append_order(self, order_data, extension, smaller_size):
        """Добавление данных в таблицу Google Sheets"""

        worksheet = self.sort_by_sheets(extension, smaller_size)
        headers = worksheet.row_values(1)

        # Получить количество видимых строк с данными
        num_rows = len(worksheet.get_all_records()) + 1  # +1 потому что первая строка - это заголовки

        row_data = ['' for _ in range(len(headers))]

        # Заполнение данных в строку
        for column, value in order_data.items():
            if column in headers:
                col_index = headers.index(column)
                row_data[col_index] = value

        # Добавить данные в первую пустую строку (независимо от скрытых строк)
        worksheet.insert_row(row_data, index=num_rows + 1)

        status_col_index = headers.index('Status') + 1  # Индексация начинается с 0, поэтому +1
        new_row_index = num_rows + 1  # Первая пустая строка, в которую добавлены данные

        # Закрашивание ячейки в колонке Status
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
                },
                # Установка стратегии обрезки текста (CLIP) для всей строки
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
