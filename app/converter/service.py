from pathlib import Path

import yaml

from app.converter.pipeline.pipeline import Pipeline, TEMP_DIR, FILENAME_SUFFIX
from app.converter.utils.helpers import expand_env_vars, get_file_name, zip_directory, delete_temp_files

CFG_DIR = Path("config")


class Converter:
    def __init__(self):
        self.converted_data = []
        self.__config = None
        self.pipeline = Pipeline()
        self.__load_config()

    def __load_config(self):
        if self.__config is None:
            with open("config/application.yaml") as f:
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

    def get_download_path(self, file_name, extension="zip"):
        return f"downloads/{file_name}.{extension}"

    def cleanup(self, file_name, extension="pdf"):
        filename = get_file_name(file_name)
        saved_files = f"{self.__config['downloads']['tex_dir']}/{filename}"
        temp_files = f"{TEMP_DIR}/{filename}{FILENAME_SUFFIX}"

        delete_temp_files([saved_files, temp_files], [f"{TEMP_DIR}/{filename}{extension}"])


service = Converter()
