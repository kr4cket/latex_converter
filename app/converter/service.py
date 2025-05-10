from pathlib import Path

import yaml

from app.converter.pipeline.ocr.formulas import FormulasExtractor
from app.converter.pipeline.ocr.tables import TablesExtractor
from app.converter.pipeline.ocr.text import TextExtractor
from app.converter.pipeline.preprocessing.images import ImagePreprocessor
from app.converter.pipeline.preprocessing.pages import PDFPreprocessor
from app.converter.pipeline.file.tex import TexExporter
from app.converter.pipeline.models.openai import AIExtractor

from app.converter.pipeline.pipeline import Pipeline, TEMP_DIR, FILENAME_SUFFIX
from app.converter.utils.helpers import expand_env_vars, get_file_name, zip_directory, delete_temp_files

CFG_DIR = Path("config")


class Converter:
    def __init__(self):
        self.converted_data = []
        self.__config = self.__load_config()
        self.pipeline = Pipeline()
        self.__init_pipeline()

    def __load_config(self):
        with open("config/application.yaml") as f:
            config = yaml.safe_load(f)
        return config

    def __init_pipeline(self):
        for pp in self.__config["pipeline"]["preprocessors"]:
            processor_class = globals()[pp["name"]]
            params = expand_env_vars(pp.get("params", {}))
            self.pipeline.add_preprocessor(processor_class(**params))

        for stage in self.__config["pipeline"]["stages"]:
            stage_class = globals()[stage["name"]]
            params = expand_env_vars(stage.get("params", {}))
            self.pipeline.add_stage(stage_class(**params))

    def convert_pdf(self, file_path):
        self.pipeline.set_file_path(file_path)
        self.pipeline.prepare()
        self.converted_data = self.pipeline.run()

    def save(self, file_path, origin_name):
        dir_files = get_file_name(file_path)
        main_dir = self.__config['downloads']['tex_dir']

        return zip_directory(f"{main_dir}/{dir_files}", origin_name)

    def get_download_path(self, file_name, extension = "zip"):
        return f"downloads/{file_name}.{extension}"

    def cleanup(self, file_name, extension = "pdf"):
        filename = get_file_name(file_name)
        saved_files = f"{self.__config['downloads']['tex_dir']}/{filename}"
        temp_files = f"{TEMP_DIR}/{filename}{FILENAME_SUFFIX}"

        delete_temp_files([saved_files, temp_files], [f"{TEMP_DIR}/{filename}{extension}"])


service = Converter()