import traceback

import yaml

from app.converter.stage.stage import Stage
from app.converter.stage.container import get_stage_class
from pathlib import Path
from app.converter.utils.helpers import get_file_name, create_dir, expand_env_vars

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)
FILENAME_SUFFIX = "_pages"


class Pipeline:
    def __init__(self):
        self.file_path = ""
        self.stages = []
        self.preprocessors = []
        self.pages_data = {}
        self.__config = None
        self.__load_config()
        self.__init_stages()
        self.__init_preprocessors()

    def __load_config(self):
        if self.__config is None:
            with open("config/application.yaml") as f:
                self.__config = yaml.safe_load(f)
        return self.__config

    def __init_stages(self):
        for stage in self.__config["pipeline"]["stages"]:
            stage_class = get_stage_class(stage["name"])
            params = expand_env_vars(stage.get("params", {}))
            self.add_stage(stage_class(**params))

    def __init_preprocessors(self):
        for pp in self.__config["pipeline"]["preprocessors"]:
            processor_class = get_stage_class(pp["name"])
            params = expand_env_vars(pp.get("params", {}))
            self.add_preprocessor(processor_class(**params))

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
