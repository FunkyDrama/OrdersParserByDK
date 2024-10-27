import os
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_config_path() -> str:
    base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.getcwd()
    return os.path.join(base_dir, 'config', '.env')


class Settings(BaseSettings):
    SHIPPING_LABEL_FOLDER: str
    TABLE_ID: str

    model_config = SettingsConfigDict(env_file=get_config_path())


settings = Settings()
