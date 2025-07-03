from pathlib import Path

import yaml

from app.converter.pipeline.pipeline import Pipeline, TEMP_DIR, FILENAME_SUFFIX
from app.converter.utils.helpers import get_file_name, zip_directory, delete_temp_files
from definitions import CONFIGURATION_PATH


CFG_DIR = Path("config")


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # При первом создании — сохраняем экземпляр
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def get_download_path(file_name, extension="zip"):
    return f"downloads/{file_name}.{extension}"


class Converter:
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.converted_data = []
        self.__config = None
        self.pipeline = Pipeline()
        self.__load_config()

    def __load_config(self):
        if self.__config is None:
            with open(CONFIGURATION_PATH) as f:
                self.__config = yaml.safe_load(f)
        return self.__config

    def convert_pdf(self, file_path):
        self.pipeline.set_file_path(file_path)
        self.pipeline.prepare()
        self.converted_data = self.pipeline.run()

    def save(self, file_path, origin_name):
        dir_files = get_file_name(file_path)
        main_dir = self.__config['downloads']['tex_dir']

        return zip_directory(f"{main_dir}/{dir_files}", origin_name)

    def cleanup(self, file_name, extension="pdf"):
        filename = get_file_name(file_name)
        saved_files = f"{self.__config['downloads']['tex_dir']}/{filename}"
        temp_files = f"{TEMP_DIR}/{filename}{FILENAME_SUFFIX}"

        delete_temp_files([saved_files, temp_files], [f"{TEMP_DIR}/{filename}{extension}"])
