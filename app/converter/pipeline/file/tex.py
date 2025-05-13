from pathlib import Path

from app.converter.stage.stage import Stage


class TexExporter(Stage):
    __dir = "results/tex"
    __prefix = "page_"

    def __init__(self, directory, output_prefix, result_data_key):
        self.__output_prefix = output_prefix
        self.__dir = Path(directory)
        self.__dir.mkdir(exist_ok=True)
        self.result_data_key = result_data_key

    def process(self, data):
        file_dir = Path(self.__dir / data['meta']['filename'])
        file_dir.mkdir(exist_ok=True)

        filename = file_dir / f"{self.__prefix}{data['number']}.tex"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data[self.result_data_key])

        return filename

    def get_name(self):
        return 'save'
