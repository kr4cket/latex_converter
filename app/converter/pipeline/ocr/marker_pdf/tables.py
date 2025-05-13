from marker.config.parser import ConfigParser
from marker.converters.table import TableConverter
from marker.models import create_model_dict

from app.converter.stage.stage import Stage


class MarkerPdfTablesExtractor(Stage):
    def __init__(self, **config):
        parser = ConfigParser(config)
        self.converter = TableConverter(
            config=parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=parser.get_processors(),
            renderer=parser.get_renderer(),
            llm_service=parser.get_llm_service()
        )

    def process(self, data: dict):
        if data['pdf'] is None:
            raise ValueError("Text extractor needs PDF file!")

        pdf_path = data['pdf']
        rendered = self.converter(pdf_path)
        tables_json_str: dict = rendered.json()

        return tables_json_str

