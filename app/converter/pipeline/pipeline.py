import traceback

from app.converter.pipeline.ocr.formulas import FormulasExtractor
from app.converter.pipeline.ocr.tables import TablesExtractor
from app.converter.pipeline.ocr.text import TextExtractor
from app.converter.pipeline.preprocessing.images import ImagePreprocessor
from app.converter.pipeline.preprocessing.pages import PDFPreprocessor
from app.converter.pipeline.file.tex import TexExporter
from app.converter.pipeline.models.openai import AIExtractor

from app.converter.stage.stage import Stage
from pathlib import Path
from app.converter.utils.helpers import get_file_name, create_dir

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

FILENAME_SUFFIX = "_pages"

class Pipeline:
    def __init__(self):
        self.file_path = ""
        self.stages = []
        self.preprocessors = []
        self.pages_data = {}

    def set_file_path(self, file_path):
        self.file_path = file_path

    def add_stage(self, stage: Stage):
        self.stages.append(stage)
        return self

    def add_preprocessor(self, preprocessor: Stage):
        self.preprocessors.append(preprocessor)
        return self

    def prepare(self):
        filename = get_file_name(self.file_path) + FILENAME_SUFFIX
        dir_name = TEMP_DIR / filename
        create_dir(dir_name)
        meta_data = {
            'filename': get_file_name(self.file_path),
            'input': self.file_path,
            'dir': dir_name,
        }

        preprocessors_data = {}
        for preprocessor in self.preprocessors:
            preprocessors_data[preprocessor.get_name()] = preprocessor.process(meta_data)

        for preprocessor in preprocessors_data:
            for data in preprocessors_data[preprocessor]:
                ind = preprocessors_data[preprocessor].index(data) + 1
                if ind not in self.pages_data:
                    self.pages_data[ind] = {}
                self.pages_data[ind][preprocessor] = data
                self.pages_data[ind]['meta'] = meta_data

    def run(self):
        page_num = 1
        try:
            for page in self.pages_data:
                if page not in self.pages_data:
                    self.pages_data[page] = {}
                self.pages_data[page]['number'] = page_num
                for stage in self.stages:
                    self.pages_data[page][stage.get_name()] = stage.process(self.pages_data[page])

                page_num += 1
        except Exception as e:
            print(f"error while working pipeline:{e}")
            traceback.print_exception(type(e), e, e.__traceback__)

        return self.pages_data