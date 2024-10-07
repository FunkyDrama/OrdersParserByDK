import os
import sys
from typing import LiteralString

from colorama import Fore, Back
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def resource_path(relative_path: LiteralString):
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

    def __init__(self):
        """Инициализация данных Google Drive"""
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.creds = service_account.Credentials.from_service_account_file(resource_path('token.json'),
                                                                           scopes=self.scopes)
        self.service = build('drive', 'v3', credentials=self.creds)

    @staticmethod
    def search_file_by_name(self, query):
        """Метод для поиска файла на диске. Принимает запрос поиска"""
        try:
            file_results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, webViewLink)').execute()

            files = file_results.get('files', [])

            if not files:
                return {"id": "File Not Found", "name": "File Not Found", "link": "File Not Found"}

            for file in files:
                file_id = file['id']
                file_link = file['webViewLink']
                filename = file['name']
                result = {"id": file_id, "name": filename, "link": file_link}
                return result

        except HttpError as error:
            print(Fore.RED + f"!!!Произошла ошибка: {error}!!!" + Back.WHITE)
            return None
