"""Searching and uploading files on Google Drive."""

import os
import sys
import threading
from typing import Any

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from config.settings import get_settings
from core.console import cprint
from core.i18n import tr
from core.constants import FILE_NOT_FOUND
from core.paths import resource_path  # noqa: F401
from google_api.auth import get_drive_service


class GoogleDriveFinder:
    """Finds files on Google Drive"""

    def __init__(self) -> None:
        """Initialization: a query cache shared between threads, guarded by a lock."""
        self._search_cache: dict[str, list[dict[str, Any]] | None] = {}
        self._cache_lock = threading.Lock()

    @property
    def service(self):
        """The Drive service of the current thread (httplib2 is not thread-safe)."""
        return get_drive_service()

    def search_file_by_name(self, query: str) -> list[dict[str, Any]] | None:
        """Searches for a file on the Drive. Takes the search query.

        Calling again with the same query within one run returns the
        cached result without touching the API.
        """
        with self._cache_lock:
            if query in self._search_cache:
                return self._search_cache[query]

        try:
            file_results = (
                self.service.files()
                .list(q=query, spaces="drive", fields="files(id, name, webViewLink)")
                .execute(num_retries=3)
            )

            files = file_results.get("files", [])
            result = [
                {"id": file["id"], "name": file["name"], "link": file["webViewLink"]}
                for file in files
            ]
            found = result if result else None
            with self._cache_lock:
                self._search_cache[query] = found
            return found

        except HttpError as error:
            cprint(tr("!!!An error occurred: {error}!!!", error=error), "error")
            return None

    def upload_shipping_labels(self, order_id: str) -> Any | None | str:
        """Uploads shipping-label files and removes them locally afterwards"""
        if getattr(sys, "frozen", False):
            current_folder = os.path.dirname(sys.executable)
        else:
            current_folder = os.getcwd()

        files_list = os.listdir(current_folder)
        shipping_label_name = f"{order_id}.pdf"

        for label in files_list:
            if shipping_label_name == label.strip():
                try:
                    file_metadata: dict[str, Any] = {"name": label}
                    folder_id = get_settings().SHIPPING_LABEL_FOLDER
                    if folder_id:
                        file_metadata["parents"] = [folder_id]

                    file_path = os.path.join(current_folder, label)
                    media = MediaFileUpload(file_path, mimetype="application/pdf")

                    file = (
                        self.service.files()
                        .create(
                            body=file_metadata,
                            media_body=media,
                            fields="id, webViewLink",
                        )
                        .execute(num_retries=3)
                    )

                    cprint(
                        f"- {tr('Shipping label uploaded')}: {file['webViewLink']}",
                        "success",
                    )

                    link = file.get("webViewLink")
                    if link:
                        del media
                        os.remove(file_path)
                    return link

                except HttpError as error:
                    cprint(tr("!!!An error occurred: {error}!!!", error=error), "error")
                    return None

        cprint(
            tr(
                "||| Check that the shipping label exists, most likely it is not in the app folder |||"
            ),
            "error",
        )
        return FILE_NOT_FOUND
