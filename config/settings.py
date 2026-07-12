"""Application settings (.env next to config/)."""

import os
import sys
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_config_path() -> str:
    base_dir = sys._MEIPASS if getattr(sys, "frozen", False) else os.getcwd()  # type: ignore[attr-defined]
    return os.path.join(base_dir, "config", ".env")


class Settings(BaseSettings):
    SHIPPING_LABEL_FOLDER: str
    TABLE_ID: str

    model_config = SettingsConfigDict(env_file=get_config_path(), extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """The single settings instance for the whole application."""
    return Settings()  # type: ignore[call-arg]


def __getattr__(name: str):
    """Backwards compatibility: ``from config.settings import settings``."""
    if name == "settings":
        return get_settings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
