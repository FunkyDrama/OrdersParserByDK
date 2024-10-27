import os
import sys
from typing import LiteralString, Any

from colorama import Fore, Back
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from config.settings import settings


def resource_path(relative_path: LiteralString) -> LiteralString:
    """ Получает путь к файлу, который упакован в exe или находится в проекте. """
    try:
        # Если программа упакована в exe
        base_path = sys._MEIPASS
    except AttributeError:
        # Если программа запускается как скрипт
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class GoogleDriveFinder:
    """Класс для поиска файлов на Google Drive"""

    def __init__(self) -> None:
        """Инициализация данных Google Drive"""
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.creds = service_account.Credentials.from_service_account_file(resource_path('config/token.json'),
                                                                           scopes=self.scopes)
        self.service = build('drive', 'v3', credentials=self.creds)

    def search_file_by_name(self, query: Any) -> list[dict[str, Any]] | None:
        """Метод для поиска файла на диске. Принимает запрос поиска"""
        try:
            file_results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, webViewLink)').execute()

            files = file_results.get('files', [])
            result = []
            if files:
                for file in files:
                    file_id = file['id']
                    file_link = file['webViewLink']
                    filename = file['name']
                    res = {"id": file_id, "name": filename, "link": file_link}
                    result.append(res)
            return result if result else None

        except HttpError as error:
            print(Fore.RED + f"!!!Произошла ошибка: {error}!!!" + Back.WHITE)
            return None

    def upload_shipping_labels(self, order_id: str) -> Any | None | str:
        """Метод для загрузки файлов шиплейблов и последующего их удаления"""
        if getattr(sys, 'frozen', False):
            current_folder = os.path.dirname(sys.executable)
        else:
            current_folder = os.getcwd()

        files_list = os.listdir(current_folder)
        shipping_label_name = f'{order_id}.pdf'

        # Флаг для отслеживания найденного файла
        file_found = False

        # Ищем файл шиплейбла
        for label in files_list:
            if shipping_label_name == label:
                file_found = True
                try:
                    file_metadata = {'name': label}
                    folder_id = settings.SHIPPING_LABEL_FOLDER
                    if folder_id:
                        file_metadata['parents'] = [folder_id]

                    # Используем полный путь к файлу
                    file_path = os.path.join(current_folder, label)
                    media = MediaFileUpload(file_path, mimetype="application/pdf")

                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id, webViewLink'
                    ).execute()

                    print(
                        Fore.GREEN +
                        f'- Шиплейбл загружен: {Fore.MAGENTA}{file["webViewLink"]}{Back.WHITE}' +
                        Back.WHITE
                    )

                    link = file.get('webViewLink')
                    if link:
                        # Используем полный путь при удалении
                        os.remove(file_path)
                    return link

                except HttpError as error:
                    print(Fore.RED + f"!!!Произошла ошибка: {error}!!!" + Back.WHITE)
                    return None

        # Если файл не найден
        if not file_found:
            print(
                Fore.RED +
                "||| Проверьте наличие шиплейбла, скорее всего его нет в папке с программой |||" +
                Back.WHITE
            )
            return 'File Not Found'
