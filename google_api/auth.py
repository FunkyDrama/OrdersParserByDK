"""Unified Google API authorization."""

import threading
from functools import lru_cache

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from gspread.http_client import BackOffHTTPClient

from core.paths import resource_path

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TOKEN_PATH = "config/token.json"


@lru_cache(maxsize=1)
def get_credentials() -> service_account.Credentials:
    """Service-account credentials with both scopes (Sheets + Drive)."""
    return service_account.Credentials.from_service_account_file(
        resource_path(TOKEN_PATH), scopes=SCOPES
    )


@lru_cache(maxsize=1)
def get_gspread_client() -> gspread.Client:
    """One gspread client per application, with retries on 429/5xx."""
    return gspread.authorize(get_credentials(), http_client=BackOffHTTPClient)


_thread_local = threading.local()


def get_drive_service():
    """The Google Drive service — one per THREAD.

    httplib2, which googleapiclient runs on, is not thread-safe, so during
    parallel parsing every worker thread needs its own service. Credentials
    are shared, service creation is cheap (cache_discovery=False) and
    happens once per thread.
    """
    service = getattr(_thread_local, "drive_service", None)
    if service is None:
        service = build(
            "drive", "v3", credentials=get_credentials(), cache_discovery=False
        )
        _thread_local.drive_service = service
    return service
